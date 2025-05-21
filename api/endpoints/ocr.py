from fastapi import APIRouter, File, UploadFile
import os
import tempfile
from src.ocr import extract_text

router = APIRouter()

@router.post("/extract/")
async def extract_ocr(file: UploadFile = File(...)):
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        return {"status": "error", "text": f"❌ File '{file.filename}' melebihi batas ukuran 5MB."}
    
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".heic", ".svg"]:
        return {"status": "error", "text": f"❌ Format '{ext}' tidak didukung."}
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
    
    text = extract_text(tmp_path)
    
    os.unlink(tmp_path)
    
    return {"status": "success", "text": text}