from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import os
import uuid
from core.orchestrator import orchestrator
from core.file_router import file_router
from db.firebase_manager import firebase_manager

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    query: str
    
class AuthRequest(BaseModel):
    email: str
    password: str

@router.post("/api/auth/register")
async def register(req: AuthRequest):
    # Check if user already exists
    existing = firebase_manager.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists. Please login.")

    user_id = str(uuid.uuid4())[:8]
    success = firebase_manager.create_user(req.email, req.password, user_id)
    if not success:
         raise HTTPException(status_code=500, detail="Database connection error. Check Firebase credentials.")

    session_id = str(uuid.uuid4())
    firebase_manager.log_session_start(user_id, session_id)
    return {"status": "success", "session_id": session_id, "user_id": user_id}

@router.post("/api/auth/login")
async def login(req: AuthRequest):
    user = firebase_manager.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please register.")
    
    if user.get("password") != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    session_id = str(uuid.uuid4())
    user_id = user.get("uid", str(uuid.uuid4())[:8])
    firebase_manager.log_session_start(user_id, session_id)
    return {"status": "success", "session_id": session_id, "user_id": user_id}

@router.post("/api/auth/logout")
async def logout(session_id: str = Form(...)):
    firebase_manager.log_session_end(session_id)
    return {"status": "success"}

from engines.rag_engine import rag_engine

@router.post("/api/upload")
async def upload_document(file: UploadFile = File(...), session_id: str = Form(...)):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "base_documents"))
    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, f"{session_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    route_result = file_router.process_document(file_path)
    # Dynamically inject the file into the active memory vectors without restarting the server!
    rag_engine.process_file(file_path, f"{session_id}_{file.filename}")
    
    return {"status": "success", "filename": file.filename, "route": route_result}

@router.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        response = orchestrator.execute_query(req.query, req.session_id, req.user_id)
        return {"response": response, "sources": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
