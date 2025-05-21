import os
import mysql.connector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from src.vector_db import load_vector_store, process_and_store_text
from src.db import get_db_connection
from config import GROQ_API_KEY, VECTOR_DB_PATH, LANGSMITH_TRACING, RAG_DOCUMENTS_PATH, MYSQL_CONFIG


embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

SUPPORTED_GROQ_MODELS = [
    "llama3-70b-8192",
    "llama3-8b-8192",
    "gemma2-9b-it",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama-guard-3-8b"
]

def get_groq_model(model_name: str = "llama3-70b-8192"):
    if model_name not in SUPPORTED_GROQ_MODELS:
        print(f"System: Model '{model_name}' tidak didukung. Menggunakan default 'llama3-70b-8192'.")
        model_name = "llama3-70b-8192"
    try:
        return ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name=model_name,
            temperature=0.0,
            max_tokens=4096
        )
    except Exception as e:
        print(f"System: Gagal memuat model '{model_name}': {str(e)}. Menggunakan default 'llama3-70b-8192'.")
        return ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama3-70b-8192",
            temperature=0.0,
            max_tokens=4096
        )

llm = get_groq_model()

try:
    vector_store = load_vector_store(VECTOR_DB_PATH, embedding_model)
except:
    vector_store = FAISS.from_texts([""], embedding_model)
    vector_store.save_local(VECTOR_DB_PATH)

def load_from_mysql():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT filename, text_content FROM documents")
        docs = cursor.fetchall()
        print(f"System: Memuat {len(docs)} dokumen dari MySQL.")
        for filename, text_content in docs:
            print(f"System: Mengindeks dokumen: {filename}")
            process_and_store_text(text_content, embedding_model, vector_store)
        print("System: Selesai memuat ulang dokumen dari MySQL ke FAISS.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"System: Gagal memuat dari MySQL: {str(e)}")

load_from_mysql()

if LANGSMITH_TRACING:
    from langsmith import Client
    langsmith_client = Client()
    print(f"System: Terhubung ke LangSmith project: {os.environ['LANGSMITH_PROJECT']}")