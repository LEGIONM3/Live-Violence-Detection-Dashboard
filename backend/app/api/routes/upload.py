from fastapi import APIRouter

router = APIRouter(prefix="/upload", tags=["upload"])

from fastapi import UploadFile, File, HTTPException
import shutil
import os
from app.services.inference.model_manager import model_manager

@router.post("/classify")
async def classify_video(file: UploadFile = File(...)):
    # Delegate validation to process_video
    pass
        
    # Save temp file
    temp_dir = "data/temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    file_path = os.path.join(temp_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Trigger inference (Mock)
    # In real app, this would process the video frame by frame
    result = await model_manager.process_video(file_path)
    
    # Clean up
    os.remove(file_path)
    
    return result
