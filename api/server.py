from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import ocr, rag, chat, coder

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ocr.router, prefix="/ocr")
app.include_router(rag.router, prefix="/rag")
app.include_router(chat.router, prefix="/chat")
app.include_router(coder.router, prefix="/coder")

@app.get("/")
def home():
    return {"message": "Multimodal Assistant API is running!"}