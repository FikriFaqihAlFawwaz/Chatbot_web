import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from models import get_groq_model
from config import LANGSMITH_TRACING
from src.db import log_to_mysql


coder_chat_history = ChatMessageHistory()

prompt_template = ChatPromptTemplate.from_messages([
    ("system", """
    System: Anda adalah asisten coding yang memberikan jawaban detail, jelas, dan terstruktur. Gunakan Markdown dan sertakan contoh kode dalam blok kode (```). 
    - Jawab hanya pertanyaan terkait coding (misalnya, membuat kode, debugging, penjelasan konsep pemrograman).
    - Jika pertanyaan tidak terkait coding, jawab: "Gunakan fitur General Chat untuk pertanyaan umum."
    - Jika pertanyaan memerlukan dokumen, jawab: "Gunakan fitur RAG System untuk pertanyaan berbasis dokumen."
    - Jika pertanyaan memerlukan OCR, jawab: "Gunakan fitur OCR untuk mengekstrak teks dari gambar."
    - Gunakan bahasa yang sama dengan input pengguna.
    """),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{query}")
])

def detect_language(query: str) -> str:
    indonesian_words = {"apa", "bagaimana", "siapa", "dimana", "kapan", "mengapa", "adalah"}
    query_lower = query.lower()
    if any(word in query_lower for word in indonesian_words):
        return "id"
    return "en"

def detect_non_coding_query(query: str) -> bool:
    non_coding_keywords = {"definisi", "pengertian", "apa itu", "sejarah", "fakta"}
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in non_coding_keywords) and "kode" not in query_lower and "code" not in query_lower

def chat_coder(query: str, model_name: str = "llama3-70b-8192"):
    if LANGSMITH_TRACING:
        print(f"System: Melacak coder query '{query}' di LangSmith.")
    
 
    language = detect_language(query)
    print(f"System: Bahasa terdeteksi: {language}")


    if detect_non_coding_query(query):
        answer = "Gunakan fitur General Chat untuk pertanyaan umum."
    else:

        llm = get_groq_model(model_name)
        chat_history = coder_chat_history.messages
        prompt = prompt_template.format_messages(query=query, chat_history=chat_history)
        response = llm.invoke(prompt)
        answer = response.content.strip()


        if len(answer.split()) > 50 and "\n" not in answer:
            answer = "\n".join([answer[i:i+100] for i in range(0, len(answer), 100)])


        coder_chat_history.add_user_message(query)
        coder_chat_history.add_ai_message(answer)


    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "input": query,
        "output": answer,
        "metadata": {
            "source": "Coder Chatbot",
            "model": model_name,
            "context": "Coding",
            "language": language
        }
    }
    log_to_mysql("coder_logs", log_entry)
    
    return answer