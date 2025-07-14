from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
from datetime import datetime
from typing import List
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MAZLABZ File Upload API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/mazlabz")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/backend/uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URL)
db = client.mazlabz
files_collection = db.files

# Pydantic models
class FileInfo(BaseModel):
    id: str
    filename: str
    original_filename: str
    size: int
    content_type: str
    upload_date: datetime
    user_session: str = None

class DashboardResponse(BaseModel):
    total_files: int
    total_size: int
    files: List[FileInfo]

# Utility functions
def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()

def is_allowed_file(filename: str) -> bool:
    allowed_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff',  # Images
        '.pdf', '.doc', '.docx', '.txt', '.rtf',  # Documents
        '.xls', '.xlsx', '.csv',  # Spreadsheets
        '.ppt', '.pptx',  # Presentations
        '.zip', '.rar', '.7z'  # Archives
    }
    return get_file_extension(filename) in allowed_extensions

# API Routes
@app.get("/")
async def root():
    return {"message": "MAZLABZ File Upload API", "version": "1.0.0"}

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload multiple files"""
    uploaded_files = []
    
    for file in files:
        try:
            # Validate file
            if not is_allowed_file(file.filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not allowed: {file.filename}"
                )
            
            # Check file size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large: {file.filename} (max {MAX_FILE_SIZE} bytes)"
                )
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = get_file_extension(file.filename)
            unique_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Save metadata to database
            file_info = {
                "id": file_id,
                "filename": unique_filename,
                "original_filename": file.filename,
                "size": len(content),
                "content_type": file.content_type,
                "upload_date": datetime.utcnow(),
                "user_session": None,  # Can be extended later
                "file_path": file_path
            }
            
            await files_collection.insert_one(file_info)
            
            uploaded_files.append({
                "id": file_id,
                "filename": file.filename,
                "size": len(content),
                "content_type": file.content_type
            })
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error uploading {file.filename}: {str(e)}")
    
    return {"message": f"Successfully uploaded {len(uploaded_files)} files", "files": uploaded_files}

@app.get("/api/files")
async def get_files():
    """Get list of uploaded files"""
    try:
        files_cursor = files_collection.find({}).sort("upload_date", -1)
        files = []
        
        async for file_doc in files_cursor:
            files.append({
                "id": file_doc["id"],
                "filename": file_doc["original_filename"],
                "size": file_doc["size"],
                "content_type": file_doc["content_type"],
                "upload_date": file_doc["upload_date"].isoformat()
            })
        
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching files: {str(e)}")

@app.get("/api/files/{file_id}")
async def download_file(file_id: str):
    """Download a specific file"""
    try:
        file_doc = await files_collection.find_one({"id": file_id})
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = file_doc["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        return FileResponse(
            file_path,
            filename=file_doc["original_filename"],
            media_type=file_doc["content_type"]
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a specific file"""
    try:
        file_doc = await files_collection.find_one({"id": file_id})
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete file from disk
        file_path = file_doc["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        await files_collection.delete_one({"id": file_id})
        
        return {"message": "File deleted successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@app.get("/api/dashboard")
async def get_dashboard():
    """Get dashboard information for admin"""
    try:
        # Get total file count
        total_files = await files_collection.count_documents({})
        
        # Get total size
        pipeline = [
            {"$group": {"_id": None, "total_size": {"$sum": "$size"}}}
        ]
        size_result = await files_collection.aggregate(pipeline).to_list(1)
        total_size = size_result[0]["total_size"] if size_result else 0
        
        # Get recent files
        files_cursor = files_collection.find({}).sort("upload_date", -1).limit(50)
        files = []
        
        async for file_doc in files_cursor:
            files.append({
                "id": file_doc["id"],
                "filename": file_doc["original_filename"],
                "size": file_doc["size"],
                "content_type": file_doc["content_type"],
                "upload_date": file_doc["upload_date"].isoformat()
            })
        
        return {
            "total_files": total_files,
            "total_size": total_size,
            "files": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)