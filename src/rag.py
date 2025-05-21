import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from models import llm, vector_store
from config import LANGSMITH_TRACING
from src.db import log_to_mysql
import logging

logging.getLogger("langchain").setLevel(logging.WARNING)

RAG_LOG_DIR = Path("data-rag/logs/archive")
RAG_LOG_DIR.mkdir(parents=True, exist_ok=True)

prompt_template = PromptTemplate(
    input_variables=["context", "question", "chat_history"],
    template="""
    System: Anda adalah asisten RAG yang HANYA menjawab berdasarkan dokumen yang diunggah. 
    - DILARANG menggunakan pengetahuan eksternal atau memberikan jawaban spekulatif.
    - Jika tidak ada dokumen relevan, jawab: "Assistant: Saya tidak memiliki informasi cukup dari dokumen yang diunggah untuk menjawab ini."
    - Gunakan bahasa yang sama dengan input pengguna.
    - Gunakan Markdown untuk formatting.
    - Berikan jawaban singkat, terstruktur, dan langsung ke inti.
    - Jika jawaban panjang, gunakan poin-poin.
    
    Riwayat percakapan:
    {chat_history}
    
    Context dari dokumen:
    {context}
    
    Pertanyaan: {question}
    Jawaban:
    """
)

stuff_chain = create_stuff_documents_chain(llm=llm, prompt=prompt_template)

def detect_language(query: str) -> str:
    indonesian_words = {"apa", "bagaimana", "siapa", "dimana", "kapan", "mengapa", "adalah"}
    query_lower = query.lower()
    if any(word in query_lower for word in indonesian_words):
        return "id"
    return "en"

def query_rag(question: str, chat_history: list = None) -> tuple[str, list]:
    if LANGSMITH_TRACING:
        print(f"System: Melacak query '{question}' di LangSmith.")
    
    language = detect_language(question)
    print(f"System: Bahasa terdeteksi: {language}")
    
    chat_history = chat_history or []
    
    print(f"System: Memahami pertanyaan RAG: {question}")


    docs = []
    try:
        retriever_no_threshold = vector_store.as_retriever(search_kwargs={"k": 10})
        docs_no_threshold = retriever_no_threshold.invoke(question)
        print(f"System: Dokumen yang diambil (tanpa ambang batas): {len(docs_no_threshold)} dokumen")
        for i, doc in enumerate(docs_no_threshold):
            score = vector_store.similarity_search_with_score(question, k=10)[i][1]
            print(f"System: Dokumen {i + 1}: {doc.page_content[:100]}... (Skor Jarak: {score})")
    except Exception as e:
        print(f"System: Gagal mengambil dokumen (tanpa ambang batas): {str(e)}")


    try:
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(question)
        print(f"System: Dokumen yang diambil untuk inferensi: {len(docs)} dokumen")
        for i, doc in enumerate(docs):
            score = vector_store.similarity_search_with_score(question, k=5)[i][1]
            print(f"System: Dokumen {i + 1}: {doc.page_content[:100]}... (Skor Jarak: {score})")
    except Exception as e:
        print(f"System: Gagal mengambil dokumen untuk inferensi: {str(e)}")


    if not docs or all(doc.page_content.strip() == "" for doc in docs):
        answer = "Assistant: Saya tidak memiliki informasi cukup dari dokumen yang diunggah untuk menjawab ini."
    else:
        print(f"System: Memproses dan menalar jawaban RAG untuk: {question}")
        
        chat_history_str = ""
        for i, msg in enumerate(chat_history):
            role = "User" if i % 2 == 0 else "Assistant"
            try:
                if isinstance(msg, dict) and "content" in msg:
                    chat_history_str += f"{role}: {msg['content']}\n"
                elif hasattr(msg, "content"):
                    chat_history_str += f"{role}: {msg.content}\n"
                else:
                    print(f"System: Format pesan riwayat tidak valid pada indeks {i}: {msg}")
                    continue
            except Exception as e:
                print(f"System: Gagal memproses pesan riwayat pada indeks {i}: {str(e)}")
                continue
        
        try:
            answer = stuff_chain.invoke({
                "context": docs,
                "question": question,
                "chat_history": chat_history_str
            }).strip()
        except Exception as e:
            print(f"System: Gagal menjalankan chain: {str(e)}")
            answer = "Assistant: Saya tidak memiliki informasi cukup dari dokumen yang diunggah untuk menjawab ini."

        if len(answer.split()) > 50 and "\n" not in answer:
            answer = "\n".join([answer[i:i+100] for i in range(0, len(answer), 100)])

    print(f"System: Memeriksa konteks jawaban RAG untuk: {question}")


    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "input": question,
        "output": answer,
        "metadata": {
            "source": "RAG System",
            "model": "llama3-70b-8192",
            "context_docs": len(docs),
            "language": language,
            "chat_history_length": len(chat_history)
        }
    }
    try:
        log_to_mysql("rag_logs", log_entry)
    except Exception as e:
        print(f"System: Gagal menyimpan log ke MySQL: {str(e)}")

    log_file = RAG_LOG_DIR / f"rag_log_{log_entry['id']}.json"
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
        print(f"System: Log disimpan ke file {log_file}")
    except Exception as e:
        print(f"System: Gagal menyimpan log ke file {log_file}: {str(e)}")

    updated_history = chat_history.copy()
    updated_history.append({"content": question})
    updated_history.append({"content": answer})
    
    return answer, updated_history