import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "data-rag/faiss_index")


RAG_DOCUMENTS_PATH = Path(os.getenv("RAG_DOCUMENTS_PATH", "data-rag/documents"))
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",  # Replace with your MySQL username
    "password": "",  # Replace with your MySQL password
    "database": "chatbot"  # Replace with your MySQL database name
}

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "multimodal-assistant")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"


MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "multimodal_assistant")
}


RAG_SUBFOLDERS = {
    ".pdf": RAG_DOCUMENTS_PATH / "pdf",
    ".doc": RAG_DOCUMENTS_PATH / "doc",
    ".docx": RAG_DOCUMENTS_PATH / "docx"
}


for folder in RAG_SUBFOLDERS.values():
    folder.mkdir(parents=True, exist_ok=True)

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY tidak ditemukan di .env")

if LANGSMITH_TRACING:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    print("System: LangSmith tracing diaktifkan.")
else:
    print("System: LangSmith tracing tidak diaktifkan.")