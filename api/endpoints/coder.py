from fastapi import APIRouter
from pydantic import BaseModel
from src.coder import chat_coder
from models import SUPPORTED_GROQ_MODELS

router = APIRouter()

class CoderRequest(BaseModel):
    query: str
    model_name: str = "llama3-70b-8192"

@router.post("/coder/")
async def coder_chat(request: CoderRequest):
    response = chat_coder(request.query, request.model_name)
    return {"query": request.query, "response": response, "model": request.model_name}