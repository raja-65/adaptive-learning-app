import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from db.supabase_client import (
    get_supabase_client,
    store_nodes,
    store_questions,
    update_file_status,
)
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, BackgroundTasks
from db.supabase_client import (
    get_supabase_client,
    store_nodes,
    store_questions,
    update_file_status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from dotenv import load_dotenv

# Import our custom modules
from processors.document_processor import process_document
from processors.knowledge_extractor import extract_knowledge_graph
from processors.question_generator import generate_questions
from db.supabase_client import get_supabase_client, store_nodes, store_questions, update_file_status

# Load environment variables
load_dotenv()

# Check if Groq API key is available
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY environment variable is not set")

app = FastAPI(title="MedLearn AI Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProcessingResponse(BaseModel):
    file_id: str
    status: str
    message: str

class Node(BaseModel):
    id: str
    title: str
    content: str
    summary: str
    prerequisites: List[str] = []

class Question(BaseModel):
    node_id: str
    question: str
    options: List[str]
    correct_answer: int
    explanation: str

@app.get("/")
async def root():
    return {"message": "MedLearn AI Backend is running"}

@app.post("/process-file", response_model=ProcessingResponse)
async def process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    """
    Process an uploaded educational document and extract knowledge graph and questions.
    This endpoint initiates background processing and returns immediately.
    """
    # Generate a unique ID for this file
    file_id = str(uuid.uuid4())
    
    # Save the file temporarily
    file_path = f"temp/{file_id}_{file.filename}"
    os.makedirs("temp", exist_ok=True)
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Store file info in Supabase
        supabase = get_supabase_client()
        supabase.table("files").insert({
            "id": file_id,
            "file_name": file.filename,
            "uploaded_by": user_id,
            "status": "processing",
        }).execute()
        
        # Process the file in the background
        background_tasks.add_task(
            process_file_background,
            file_path=file_path,
            file_name=file.filename,
            file_id=file_id,
            user_id=user_id
        )
        
        return {
            "file_id": file_id,
            "status": "processing",
            "message": "File uploaded and processing started"
        }
    
    except Exception as e:
        # Update file status to error
        update_file_status(file_id, "error", str(e))
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

async def process_file_background(file_path: str, file_name: str, file_id: str, user_id: str):
    """Background task to process the document and extract knowledge"""
    try:
        # Extract text from document
        text = process_document(file_path)
        
        # Extract knowledge graph
        nodes = extract_knowledge_graph(text)
        
        # Generate questions for each node
        all_questions = []
        for node in nodes:
            questions = generate_questions(node)
            all_questions.extend(questions)
        
        # Store nodes and questions in Supabase
        store_nodes(nodes, file_id, user_id)
        store_questions(all_questions)
        
        # Update file status
        update_file_status(
            file_id, 
            "processed", 
            f"Successfully extracted {len(nodes)} nodes and {len(all_questions)} questions"
        )
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        # Update file status to error
        update_file_status(file_id, "error", str(e))
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/status/{file_id}")
async def get_processing_status(file_id: str):
    """Get the status of a file processing job"""
    supabase = get_supabase_client()
    response = supabase.table("files").select("*").eq("id", file_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="File not found")
    
    return response.data[0]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
