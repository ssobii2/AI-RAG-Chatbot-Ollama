import os
import json
import uvicorn
import uuid
from collections import defaultdict
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage, SystemMessage
from fastapi import FastAPI, HTTPException, Path, Request
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
chat_sessions_dir = os.path.join(current_dir, "chat_sessions")

print(f"PDFs directory: {pdfs_dir}")
print(f"Persistent directory: {persistent_directory}")

if not os.path.exists(chat_sessions_dir):
    os.makedirs(chat_sessions_dir)

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
        chunk_size=2000, chunk_overlap=100
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

# Using a smaller model for faster response times and testing
# You can uncomment the line below to use the larger model
# Also make sure you have the larger model downloaded by running `ollama pull llama3.1`
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

# Store session titles
session_titles = defaultdict(str)

# Title Generation Prompt
title_generation_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that generates concise, clear, and descriptive titles. Given the user query below, generate a title that summarizes the main topic or request of the query in 3 to 6 words."),
        ("human", "{input}"),
    ]
)

def generate_title(llm, query):
    prompt = title_generation_prompt.invoke({"input": query})
    result = llm.invoke(prompt)
    return result.content

# Function to load chat history from a file
def load_chat_history(session_id):
    session_file = os.path.join(chat_sessions_dir, f"{session_id}.json")
    if os.path.exists(session_file):
        with open(session_file, "r") as file:
            session_data = json.load(file)
            session_titles[session_id] = session_data.get("title", session_titles.get(session_id, "Untitled Session"))
            return [
                HumanMessage(content=msg["content"]) if msg["type"] == "human" else SystemMessage(content=msg["content"])
                for msg in session_data.get("history", [])
            ]
    return []

# Function to save chat history to a file
def save_chat_history(session_id, chat_history):
    session_file = os.path.join(chat_sessions_dir, f"{session_id}.json")
    with open(session_file, "w") as file:
        json.dump({
            "title": session_titles[session_id],
            "history": [{"type": "human" if isinstance(msg, HumanMessage) else "system", "content": msg.content} for msg in chat_history]
        }, file)

class QueryRequest(BaseModel):
    query: str
    session_id: str

class CreateSessionResponse(BaseModel):
    session_id: str
    session_url: str
    title: str

@app.post("/create_chat_session", response_model=CreateSessionResponse)
async def create_chat_session(request: Request):
    session_id = str(uuid.uuid4())
    session_title = f"Session {len(session_titles) + 1}"
    session_titles[session_id] = session_title
    
    save_chat_history(session_id, [])
    base_url = str(request.url_for("create_chat_session")).replace("create_chat_session", f"chat/{session_id}")
    return {"session_id": session_id, "session_url": base_url, "title": session_title}

@app.post("/chat")
async def chat_endpoint(request: QueryRequest):
    query = request.query
    session_id = request.session_id

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID cannot be empty")

    chat_history = load_chat_history(session_id)

    new_title = False
    if session_titles[session_id].startswith("Session"):
        session_titles[session_id] = generate_title(llm, query)
        new_title = True

    result = rag_chain.invoke({"input": query, "chat_history": chat_history})
    
    chat_history.append(HumanMessage(content=query))
    chat_history.append(SystemMessage(content=result["answer"]))
    save_chat_history(session_id, chat_history)

    return {"answer": result['answer'], "title": session_titles[session_id] if new_title else None}

@app.get("/chat_history/{session_id}")
async def get_chat_history(session_id: str = Path(..., description="The ID of the session to retrieve chat history for")):
    chat_history = load_chat_history(session_id)
    return [
        {"type": "human" if isinstance(msg, HumanMessage) else "system", "content": msg.content}
        for msg in chat_history
    ]

@app.get("/chat_sessions")
async def get_chat_sessions():
    if not os.path.exists(chat_sessions_dir):
        return []

    sessions = []
    for session_file in os.listdir(chat_sessions_dir):
        session_id, ext = os.path.splitext(session_file)
        if ext == ".json":
            with open(os.path.join(chat_sessions_dir, session_file), "r") as file:
                session_data = json.load(file)
                title = session_data.get("title", f"Session {session_id}")
                session_titles[session_id] = title
                sessions.append({"session_id": session_id, "title": title})
    return sessions

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)