import os
import json
import uvicorn
import uuid
import shutil
import base64
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, UnstructuredExcelLoader, JSONLoader, UnstructuredImageLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

os.environ["OPENAI_API_KEY"] = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Set the environment variable to disable anonymized telemetry for Chroma
os.environ["ANONYMIZED_TELEMETRY"] = "False"

app = FastAPI()

app.include_router(router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

current_dir = os.path.dirname(os.path.abspath(__file__))
files_dir = os.path.join(current_dir, "files")
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.join(db_dir, "chroma_db_with_metadata")
processed_files_file = os.path.join(db_dir, "processed_files.json")
metadata_file = os.path.join(db_dir, "metadata.json")

print(f"Files directory: {files_dir}")
print(f"Persistent directory: {persistent_directory}")

def load_processed_files():
    if os.path.exists(processed_files_file):
        with open(processed_files_file, "r") as file:
            return json.load(file)
    return []

def save_processed_files(processed_files):
    with open(processed_files_file, "w") as file:
        json.dump(processed_files, file)

def load_metadata():
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as file:
            return json.load(file)
    return {}

def save_metadata(metadata):
    with open(metadata_file, "w") as file:
        json.dump(metadata, file)

def delete_db_contents():
    if os.path.exists(db_dir):
        for filename in os.listdir(db_dir):
            file_path = os.path.join(db_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
        print(f"\nDeleted the contents of the directory: {db_dir}")

def update_vector_store():
    global db
    try:
        processed_files = load_processed_files()
        metadata = load_metadata()

        # List all files in the directory
        all_files = [f for f in os.listdir(files_dir) if f.endswith(('.pdf', '.csv', '.xlsx', '.json', '.jpg', '.jpeg', '.png'))]

        # Identify new files
        new_files = [f for f in all_files if f not in processed_files]

        # Identify deleted files
        deleted_files = [f for f in processed_files if f not in all_files]

        # Initialize vector store
        if os.path.exists(persistent_directory):
            print("\nLoading existing vector store")
            db = Chroma(embedding_function=OllamaEmbeddings(base_url="http://ollama:11434", model="nomic-embed-text"), persist_directory=persistent_directory)
        else:
            print("\nCreating new vector store")
            db = Chroma(embedding_function=OllamaEmbeddings(base_url="http://ollama:11434", model="nomic-embed-text"), persist_directory=persistent_directory)

        if not new_files and not deleted_files:
            print("\nNo changes detected in files.")
            return

        # Process new files if present
        if new_files:
            print(f"\nNew files detected: {new_files}")

            documents = []
            chunk_metadata = {}
            for file in new_files:
                file_path = os.path.join(files_dir, file)
                if file.endswith(".pdf"):
                    print(f"Loading PDF file: {file_path}")
                    loader = PyPDFLoader(file_path)
                    pdf_docs = loader.load()
                    print(f"Loaded {len(pdf_docs)} documents from {file_path}")
                    for doc in pdf_docs:
                        doc.metadata = {"source": file}
                        documents.append(doc)
                elif file.endswith(".csv"):
                    print(f"Loading CSV file: {file_path}")
                    loader = CSVLoader(file_path, csv_args={'delimiter': ','})
                    csv_docs = loader.load()
                    print(f"Loaded {len(csv_docs)} documents from {file_path}")
                    for doc in csv_docs:
                        doc.metadata = {"source": file}
                        documents.append(doc)
                elif file.endswith(".xlsx"):
                    print(f"Loading Excel file: {file_path}")
                    loader = UnstructuredExcelLoader(file_path)
                    excel_docs = loader.load()
                    print(f"Loaded {len(excel_docs)} documents from {file_path}")
                    for doc in excel_docs:
                        doc.metadata = {"source": file}
                        documents.append(doc)
                elif file.endswith(".json"):
                    print(f"Loading JSON file: {file_path}")
                    # loader = JSONLoader(file_path, text_content=False, jq_schema=".[]")
                    loader = JSONLoader(file_path, text_content=False, jq_schema=".")
                    json_docs = loader.load()
                    print(f"Loaded {len(json_docs)} documents from {file_path}")
                    for doc in json_docs:
                        doc.metadata = {"source": file}
                        documents.append(doc)
                elif file.endswith((".png", ".jpg", ".jpeg")):
                    print(f"Processing image: {file_path}")

                    with open(file_path, "rb") as image_file:
                        image_data = base64.b64encode(image_file.read()).decode("utf-8")

                    message = HumanMessage(
                        content=[
                            {"type": "text", "text": "Describe the content of this image."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                            },
                        ]
                    )
                    ai_msg = image_llm.invoke([message])
                    description_text = ai_msg.content
                    print(f"Image description: {description_text}")
                    doc = Document(page_content=description_text, metadata={"source": file})
                    documents.append(doc)

            rec_char_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            )
            rec_char_docs = rec_char_splitter.split_documents(documents)

            print("\nDocument Chunks Information")
            print(f"Number of document chunks: {len(rec_char_docs)}")

            # Generate unique IDs for each document chunk
            ids = [str(uuid.uuid4()) for _ in range(len(rec_char_docs))]

            # Map each chunk ID to its corresponding source file
            for chunk_id, chunk in zip(ids, rec_char_docs):
                chunk_metadata[chunk_id] = chunk.metadata["source"]

            print("\nAdding new document chunks to the vector store")
            db.add_documents(documents=rec_char_docs, ids=ids)

            # Update metadata with new IDs
            metadata.update(chunk_metadata)

        if deleted_files:
            print(f"\nDeleted files detected: {deleted_files}")

            # Find vector IDs related to deleted files
            ids_to_delete = [id for id, source in metadata.items() if source in deleted_files]
            if ids_to_delete:
                print(f"\nDeleting vectors with IDs: {ids_to_delete}")
                db.delete(ids_to_delete)
                
                # Remove deleted files from metadata and processed_files
                metadata = {id: source for id, source in metadata.items() if source not in deleted_files}
                processed_files = [file for file in processed_files if file not in deleted_files]

        print("\nFinished updating vector store")

        # Update processed files and metadata
        processed_files.extend(new_files)
        save_processed_files(processed_files)
        save_metadata(metadata)

        print("\nProcessed files and metadata updated")

    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        delete_db_contents()
        db = None
        raise

# Initialize `db` and retriever
db = None
retriever = None

if not os.path.exists(persistent_directory):
    print("\nPersistent directory does not exist. Initializing vector store...")
    update_vector_store()
else:
    print("Vector store already exists. Loading existing vector store.")
    model_name = "nomic-embed-text"
    embeddings = OllamaEmbeddings(base_url="http://ollama:11434", model=model_name)
    db = Chroma(embedding_function=embeddings, persist_directory=persistent_directory)

    # After loading, check for new files and update the vector store if needed
    update_vector_store()

# Initialize retriever after `db` is properly set up
if db is not None:
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5},
    )
    # retriever = db.as_retriever(
    #     search_type="mmr",
    #     search_kwargs={"k": 3, "fetch_k": 20, "lambda_mult": 0.5},
    # )

# Using a smaller model for faster response times and testing
# You can uncomment the line below to use the larger model
# Also make sure you have the larger model downloaded by running `ollama pull llama3.1`
# text_llm = ChatOllama(base_url="http://ollama:11434", model="qwen2:1.5b")
# text_llm = ChatOllama(base_url="http://ollama:11434", model="llama3.1")
text_llm = ChatOpenAI(model="gpt-4o")
# image_llm = ChatOllama(base_url="http://ollama:11434", model="llava-phi3")
image_llm = ChatOpenAI(model="gpt-4o")

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
text_history_aware_retriever = create_history_aware_retriever(
    text_llm, retriever, contextualize_q_prompt
)

image_history_aware_retriever = create_history_aware_retriever(
    image_llm, retriever, contextualize_q_prompt
)

# Answer question prompt
# This system prompt helps the AI understand that it should provide concise answers
# based on the retrieved context and indicates what to do if the answer is unknown
qa_system_prompt = (
    "You are an assistant for question-answering tasks. Use "
    "the following pieces of retrieved context to answer the "
    "question. If you don't know the answer, just say that you "
    "don't know."
    "\n\n"
    "{context}"
)

# Create a prompt template for answering questions
qa_prompt_text = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

qa_prompt_image = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# Create a chain to combine documents for question answering
# `create_stuff_documents_chain` feeds all retrieved context into the LLM
text_question_answer_chain = create_stuff_documents_chain(text_llm, qa_prompt_text)
image_question_answer_chain = create_stuff_documents_chain(image_llm, qa_prompt_image)

# Create a retrieval chain that combines the history-aware retriever and the question answering chain
text_rag_chain = create_retrieval_chain(text_history_aware_retriever, text_question_answer_chain)
image_rag_chain = create_retrieval_chain(image_history_aware_retriever, image_question_answer_chain)

# Title Generation Prompt
title_generation_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that generates concise, clear, and descriptive titles. Given the user query below, generate a title that summarizes the main topic or request of the query in 3 to 4 words. Do not exceed the word limit and keep the title clear and concise."),
        ("human", "{input}"),
    ]
)

# Define prompt for query classification
intent_detection_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an assistant that determines if a question is asking about an image or text. If it's related to an image, respond with 'image'. If it's text-related, respond with 'text'."),
    ("human", "{input}")
])

def is_image_query(llm, query):
    prompt = intent_detection_prompt.invoke({"input": query})
    response = llm.invoke(prompt)
    print(f"Response: {response.content}")
    return response.content.strip().lower() == "image"

def generate_title(llm, query):
    prompt = title_generation_prompt.invoke({"input": query})
    result = llm.invoke(prompt)
    return result.content

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)