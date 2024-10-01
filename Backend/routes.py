import os
import json
import uuid
import shutil
import whisper
from fastapi import HTTPException, Path, Request, UploadFile, File, WebSocket, WebSocketDisconnect, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from collections import defaultdict
from langchain_core.messages import HumanMessage, SystemMessage

current_dir = os.path.dirname(os.path.abspath(__file__))
chat_sessions_dir = os.path.join(current_dir, "chat_sessions")
files_dir = os.path.join(current_dir, "files")

if not os.path.exists(chat_sessions_dir):
    os.makedirs(chat_sessions_dir)

# Initialize openai-whisper model
whisper_model = whisper.load_model("base")

# Store session titles
session_titles = defaultdict(str)

# Router instance
router = APIRouter()

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

@router.post("/create_chat_session", response_model=CreateSessionResponse)
async def create_chat_session(request: Request):
    session_id = str(uuid.uuid4())
    session_title = f"Session {len(session_titles) + 1}"
    session_titles[session_id] = session_title
    
    save_chat_history(session_id, [])
    base_url = str(request.url_for("create_chat_session")).replace("create_chat_session", f"chat/{session_id}")
    return {"session_id": session_id, "session_url": base_url, "title": session_title}

@router.post("/chat")
async def chat_endpoint(request: QueryRequest):
    from chatbot import generate_title, text_rag_chain, image_rag_chain, text_llm, image_llm, is_image_query  # Lazy import to avoid circular dependency

    query = request.query
    session_id = request.session_id

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID cannot be empty")

    chat_history = load_chat_history(session_id)

    new_title = False

    # Check if the query is for an image
    if is_image_query(text_llm, query):
        if session_titles[session_id].startswith("Session"):
            session_titles[session_id] = generate_title(text_llm, query)
            new_title = True

        result = image_rag_chain.invoke({"input": query, "chat_history": chat_history})
    else:
        if session_titles[session_id].startswith("Session"):
            session_titles[session_id] = generate_title(text_llm, query)
            new_title = True

        result = text_rag_chain.invoke({"input": query, "chat_history": chat_history})

    for doc in result["context"]:
        print(f"Source: {doc.metadata['source']}")
        print("Content:")
        print(doc.page_content)
        print("\n" + "-"*80 + "\n")
    
    chat_history.append(HumanMessage(content=query))
    chat_history.append(SystemMessage(content=result["answer"]))
    save_chat_history(session_id, chat_history)

    return {"answer": result['answer'], "title": session_titles[session_id] if new_title else None}

@router.get("/chat_history/{session_id}")
async def get_chat_history(session_id: str = Path(..., description="The ID of the session to retrieve chat history for")):
    chat_history = load_chat_history(session_id)
    return [
        {"type": "human" if isinstance(msg, HumanMessage) else "system", "content": msg.content}
        for msg in chat_history
    ]

@router.get("/chat_sessions")
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

@router.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    from chatbot import update_vector_store  # Lazy import to avoid circular dependency

    # Validate file type and extension
    valid_types = {
        "pdf": "application/pdf",
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }

    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in valid_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if file.content_type != valid_types[file_ext]:
        raise HTTPException(status_code=400, detail=f"Invalid content type for {file_ext.upper()} files")
    
    file_path = os.path.join(files_dir, file.filename)
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Update the vector store to include the new file
        update_vector_store()
        
        return {"filename": file.filename, "message": f"{file_ext.upper()} file uploaded successfully"}
    
    except Exception as e:
        if os.path.exists(file_path):
            os.unlink(file_path)
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the file: {str(e)}")

@router.delete("/delete_file/{filename}")
async def delete_file(filename: str):
    from chatbot import update_vector_store  # Lazy import to avoid circular dependency

    file_path = os.path.join(files_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete the file
    os.remove(file_path)
    
    # Update the vector store to remove the file
    update_vector_store()
    
    return {"filename": filename, "message": "File deleted successfully"}

@router.delete("/delete_chat_session/{session_id}")
async def delete_chat_session(session_id: str = Path(..., description="The ID of the session to delete")):
    session_file = os.path.join(chat_sessions_dir, f"{session_id}.json")
    if os.path.exists(session_file):
        os.remove(session_file)
        return {"session_id": session_id, "message": "Chat session deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Chat session not found")

@router.get("/list_files")
async def list_files():
    try:
        files = {
            "pdf_files": [f for f in os.listdir(files_dir) if f.endswith('.pdf')],
            "csv_files": [f for f in os.listdir(files_dir) if f.endswith('.csv')],
            "xlsx_files": [f for f in os.listdir(files_dir) if f.endswith('.xlsx')],
            "xls_files": [f for f in os.listdir(files_dir) if f.endswith('.xls')],
            "json_files": [f for f in os.listdir(files_dir) if f.endswith('.json')],
            "jpg_files": [f for f in os.listdir(files_dir) if f.endswith('.jpg')],
            "jpeg_files": [f for f in os.listdir(files_dir) if f.endswith('.jpeg')],
            "png_files": [f for f in os.listdir(files_dir) if f.endswith('.png')],
        }
        # Flatten the lists into a single list
        all_files = [file for sublist in files.values() for file in sublist]
        return JSONResponse(content=all_files)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@router.websocket("/ws/audio_chat")
async def websocket_audio_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    audio_file = f"temp_audio_{session_id}.wav"

    try:
        while True:
            data = await websocket.receive_bytes()

            # Write received audio data to file
            with open(audio_file, "wb") as f:
                f.write(data)

            # Transcribe the audio
            result = whisper_model.transcribe(audio_file)
            text_query = result['text']

            # Send the transcription back to the client
            await websocket.send_text(text_query)

            # Delete the temporary file after sending the response
            if os.path.exists(audio_file):
                os.remove(audio_file)

    except WebSocketDisconnect:
        print(f"Client {session_id} disconnected")
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
        # Ensure temporary file is deleted even if an error occurs
        if os.path.exists(audio_file):
            os.remove(audio_file)