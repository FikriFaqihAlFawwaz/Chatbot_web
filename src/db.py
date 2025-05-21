import mysql.connector
import json
from config import MYSQL_CONFIG
import uuid
from datetime import datetime

def get_db_connection():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"System: Gagal terhubung ke MySQL: {str(e)}")
        raise e

def save_document_to_mysql(filename: str, file_type: str, text_content: str):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO documents (filename, file_format, text_content, uploaded_at)
        VALUES (%s, %s, %s, NOW())
        """
        cursor.execute(query, (filename, file_type, text_content))
        conn.commit()
        print(f"System: Berhasil menyimpan dokumen {filename} ke MySQL.")
    except mysql.connector.Error as e:
        print(f"System: Gagal menyimpan dokumen ke MySQL: {str(e)}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def save_ocr_note(filename: str, extracted_text: str):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        note_id = str(uuid.uuid4())
        query = """
        INSERT INTO ocr_notes (id, filename, extracted_text)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (note_id, filename, extracted_text))
        conn.commit()
        print(f"System: Berhasil menyimpan catatan OCR untuk {filename} ke MySQL.")
    except mysql.connector.Error as e:
        print(f"System: Gagal menyimpan catatan OCR ke MySQL: {str(e)}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def log_to_mysql(table: str, log_entry: dict):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"""
        INSERT INTO {table} (id, timestamp, input, output, metadata)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            log_entry["id"],
            log_entry["timestamp"],
            log_entry["input"],
            log_entry["output"],
            json.dumps(log_entry["metadata"])
        ))
        conn.commit()
        print(f"System: Berhasil menyimpan log ke tabel {table}.")
    except mysql.connector.Error as e:
        print(f"System: Gagal menyimpan log ke MySQL: {str(e)}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()