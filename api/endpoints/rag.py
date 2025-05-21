import os
import uuid
from fastapi import APIRouter, UploadFile, HTTPException
from typing import List
from pathlib import Path
import pypandoc
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import re
import mysql.connector
import urllib3
from src.rag import query_rag
from src.vector_db import process_and_store_text
from models import embedding_model, vector_store
from config import RAG_SUBFOLDERS, RAG_DOCUMENTS_PATH, MYSQL_CONFIG
from src.db import save_document_to_mysql
from pydantic import BaseModel
from src.document_processor import extract_text as extract_text_fallback

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    chat_history: list = None

def clean_text(text: str) -> str:
    text = re.sub(r'[^\w\s.,!?()-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_text_with_ocr(file_path: Path) -> str:
    try:
        images = convert_from_path(file_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image, lang='eng+ind') + "\n"
        return text.strip()
    except Exception as e:
        print(f"System: Gagal mengekstrak teks dengan OCR: {str(e)}")
        return ""

@router.post("/upload/")
async def upload_files(files: List[UploadFile], skip_duplicates: bool = False):
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    results = []
    system_message = (
        "System: Fitur RAG System aktif. Saya akan memproses file dokumen (DOC, DOCX, PDF) "
        "untuk mengekstrak teks dan menyimpannya ke basis pengetahuan (FAISS). Metadata dan teks disimpan di MySQL. "
        "Batasan: Maksimal 10 MB per file."
    )
    print(system_message)

    RAG_DOCUMENTS_PATH.mkdir(parents=True, exist_ok=True)

    for file in files:
        filename = file.filename
        try:
            file_content = await file.read()
            file_size = len(file_content)
            if file_size > MAX_FILE_SIZE:
                results.append({
                    "status": "error",
                    "filename": filename,
                    "text": f"❌ Error: File '{filename}' melebihi batas ukuran 10MB."
                })
                continue

            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext not in RAG_SUBFOLDERS:
                results.append({
                    "status": "error",
                    "filename": filename,
                    "text": f"❌ Error: Format '{ext}' tidak didukung."
                })
                continue

            try:
                conn = mysql.connector.connect(**MYSQL_CONFIG)
                cursor = conn.cursor()
                cursor.execute("SELECT filename FROM documents WHERE filename = %s", (filename,))
                is_duplicate = cursor.fetchone() is not None
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"System: Gagal memeriksa duplikat di MySQL: {str(e)}")
                results.append({
                    "status": "error",
                    "filename": filename,
                    "text": f"❌ Error: Gagal memeriksa duplikat di database."
                })
                continue

            if skip_duplicates and is_duplicate:
                results.append({
                    "status": "skipped",
                    "filename": filename,
                    "text": f"⚠️ File '{filename}' dilewati karena sudah ada."
                })
                continue

            final_filename = filename
            if is_duplicate and not skip_duplicates:
                base, ext = os.path.splitext(filename)
                counter = 1
                while counter <= 100:
                    final_filename = f"{base}-{counter}{ext}"
                    file_path = RAG_SUBFOLDERS[ext] / final_filename
                    try:
                        conn = mysql.connector.connect(**MYSQL_CONFIG)
                        cursor = conn.cursor()
                        cursor.execute("SELECT filename FROM documents WHERE filename = %s", (final_filename,))
                        is_duplicate = cursor.fetchone() is not None
                        cursor.close()
                        conn.close()
                        if not is_duplicate:
                            break
                    except Exception as e:
                        print(f"System: Gagal memeriksa duplikat untuk {final_filename}: {str(e)}")
                        break
                    counter += 1
                if counter > 100:
                    results.append({
                        "status": "error",
                        "filename": filename,
                        "text": f"❌ Error: Gagal menemukan nama unik setelah 100 percobaan."
                    })
                    continue

            file_path = RAG_SUBFOLDERS[ext] / final_filename
            file_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                with open(file_path, "wb") as f:
                    f.write(file_content)
            except Exception as e:
                print(f"System: Gagal menyimpan file {final_filename}: {str(e)}")
                results.append({
                    "status": "error",
                    "filename": final_filename,
                    "text": f"❌ Error: Gagal menyimpan file ke disk."
                })
                continue

            text_content = ""
            file_extension = Path(final_filename).suffix.lower()

            if file_extension == ".pdf":
                try:
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_content += page_text + "\n"
                except Exception as e:
                    print(f"System: Gagal mengekstrak teks dari PDF dengan pdfplumber: {str(e)}")

                if not text_content.strip():
                    print(f"System: Teks dari pdfplumber kosong, menggunakan OCR untuk {final_filename}.")
                    text_content = extract_text_with_ocr(file_path)

            else:
                try:
                    text_content = extract_text_fallback(str(file_path))
                    if text_content.startswith("❌ Error"):
                        print(f"System: Fallback ke document_processor gagal untuk {final_filename}: {text_content}")
                        try:
                            pypandoc.ensure_pandoc_installed()
                            text_content = pypandoc.convert_file(str(file_path), "plain")
                        except Exception as e:
                            print(f"System: Gagal mengekstrak teks dengan pypandoc: {str(e)}")
                            results.append({
                                "status": "error",
                                "filename": final_filename,
                                "text": f"❌ Error: Gagal mengekstrak teks: {str(e)}"
                            })
                            continue
                except Exception as e:
                    print(f"System: Gagal mengekstrak teks dengan fallback: {str(e)}")
                    results.append({
                        "status": "error",
                        "filename": final_filename,
                        "text": f"❌ Error: Gagal mengekstrak teks: {str(e)}"
                    })
                    continue

            if not text_content.strip():
                results.append({
                    "status": "error",
                    "filename": final_filename,
                    "text": "❌ Error: Tidak ada teks yang dapat diekstrak dari file."
                })
                continue

            text_content = clean_text(text_content)
            try:
                save_document_to_mysql(final_filename, file_extension, text_content)
            except Exception as e:
                print(f"System: Gagal menyimpan dokumen {final_filename} ke MySQL: {str(e)}")
                results.append({
                    "status": "error",
                    "filename": final_filename,
                    "text": f"❌ Error: Gagal menyimpan dokumen ke database."
                })
                continue

            try:
                process_and_store_text(text_content, embedding_model, vector_store)
            except Exception as e:
                print(f"System: Gagal menyimpan teks ke FAISS untuk {final_filename}: {str(e)}")
                results.append({
                    "status": "error",
                    "filename": final_filename,
                    "text": f"❌ Error: Gagal menyimpan teks ke basis pengetahuan."
                })
                continue

            preview = text_content[:100].replace("\n", " ") + "..." if len(text_content) > 100 else text_content
            results.append({
                "status": "success",
                "filename": final_filename,
                "text": f"Teks berhasil diekstrak dari {final_filename}.",
                "preview": preview
            })

        except Exception as e:
            print(f"System: Gagal memproses file {filename}: {str(e)}")
            results.append({
                "status": "error",
                "filename": filename,
                "text": f"❌ Error: Gagal memproses file: {str(e)}"
            })

    return {"system_message": system_message, "results": results}

@router.post("/query/")
async def query(request: QueryRequest):
    try:
        answer, updated_history = query_rag(request.question, request.chat_history)
        return {"question": request.question, "answer": answer, "chat_history": updated_history}
    except Exception as e:
        print(f"System: Gagal memproses query RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses query: {str(e)}")