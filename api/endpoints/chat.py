from fastapi import APIRouter
from pydantic import BaseModel
from src.chat import chat_general
from models import SUPPORTED_GROQ_MODELS

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    model_name: str = "llama3-70b-8192"

@router.post("/general/")
async def chat(request: ChatRequest):
    response = chat_general(request.query, request.model_name)
    return {"query": request.query, "response": response, "model": request.model_name}