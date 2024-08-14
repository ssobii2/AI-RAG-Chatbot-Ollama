import os
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage, SystemMessage
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

current_dir = os.path.dirname(os.path.abspath(__file__))
pdfs_dir = os.path.join(current_dir, "pdfs")
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.join(db_dir, "chroma_db_with_metadata")
chat_history_file = os.path.join(current_dir, "chat_history.json")

print(f"PDFs directory: {pdfs_dir}")
print(f"Persistent directory: {persistent_directory}")

if not os.path.exists(persistent_directory):
    print("\nPersistent directory does not exist. Initializing vector store...")

    if not os.path.exists(pdfs_dir):
        raise FileNotFoundError(
            f"The file {pdfs_dir} does not exist. Please check the path."
        )
    
    # List all text files in the directory
    pdf_files = [f for f in os.listdir(pdfs_dir) if f.endswith(".pdf")]

    # Read the text content from each file and store it with metadata
    documents = []
    for pdf_file in pdf_files:
        file_path = os.path.join(pdfs_dir, pdf_file)
        loader = PyPDFLoader(file_path)
        pdf_docs = loader.load()
        for doc in pdf_docs:
            doc.metadata = {"source": pdf_file}
            documents.append(doc)

    rec_char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=100
    )
    rec_char_docs = rec_char_splitter.split_documents(documents)

    print("\nDocument Chunks Information")
    print(f"Number of document chunks: {len(rec_char_docs)}")

    model_name = "nomic-embed-text"
    embeddings = OllamaEmbeddings(model=model_name)

    print("\nCreating vector store")

    db = Chroma.from_documents(
        rec_char_docs,
        embeddings,
        persist_directory=persistent_directory
    )

    print("\nFinished creating vector store")
else:
    print("Vector store already exists. Loading existing vector store.")
    model_name = "nomic-embed-text"
    embeddings = OllamaEmbeddings(model=model_name)
    db = Chroma(embedding_function=embeddings, persist_directory=persistent_directory)

retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 3, "lambda_mult": 0.5},
)

# llm = ChatOllama(model="llama3.1")
llm = ChatOllama(model="qwen2:0.5b")

# Contextualize question prompt
# This system prompt helps the AI understand that it should reformulate the question
# based on the chat history to make it a standalone question
contextualize_q_system_prompt = (
    "Given the chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, just "
    "reformulate it if needed and otherwise return it as is."
)

# Create a prompt template for contextualizing questions
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# Create a history-aware retriever
# This uses the LLM to help reformulate the question based on chat history
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

# Answer question prompt
# This system prompt helps the AI understand that it should provide concise answers
# based on the retrieved context and indicates what to do if the answer is unknown
qa_system_prompt = (
    "You are an assistant for question-answering tasks. Use "
    "the following pieces of retrieved context to answer the "
    "question. If you don't know the answer, just say that you "
    "don't know. Use three sentences maximum and keep the answer "
    "concise."
    "\n\n"
    "{context}"
)

# Create a prompt template for answering questions
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# Create a chain to combine documents for question answering
# `create_stuff_documents_chain` feeds all retrieved context into the LLM
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

# Create a retrieval chain that combines the history-aware retriever and the question answering chain
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# Function to load chat history from a file
def load_chat_history():
    if os.path.exists(chat_history_file):
        with open(chat_history_file, "r") as file:
            chat_history = json.load(file)
            # Convert the loaded JSON objects back to the correct message types
            return [
                HumanMessage(content=msg["content"]) if msg["type"] == "human" else SystemMessage(content=msg["content"])
                for msg in chat_history
            ]
    return []

# Function to save chat history to a file
def save_chat_history(chat_history):
    with open(chat_history_file, "w") as file:
        # Convert the chat history to JSON serializable format
        json.dump([{"type": "human" if isinstance(msg, HumanMessage) else "system", "content": msg.content} for msg in chat_history], file)

class QueryRequest(BaseModel):
    query: str

@app.post("/chat")
async def chat_endpoint(request: QueryRequest):
    query = request.query
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Load chat history
    chat_history = load_chat_history()
    
    # Process the query using the RAG chain
    result = rag_chain.invoke({"input": query, "chat_history": chat_history})
    
    # Update chat history and save
    chat_history.append(HumanMessage(content=query))
    chat_history.append(SystemMessage(content=result["answer"]))
    save_chat_history(chat_history)
    
    return {"answer": result['answer']}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
