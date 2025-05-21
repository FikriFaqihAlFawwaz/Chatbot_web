from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import VECTOR_DB_PATH

def load_vector_store(vector_db_path: str, embedding_model):
    try:
        return FAISS.load_local(vector_db_path, embedding_model, allow_dangerous_deserialization=True)
    except Exception as e:
        print(f"System: Gagal memuat vector store: {str(e)}. Membuat vector store baru.")
        return FAISS.from_texts([""], embedding_model)

def process_and_store_text(text: str, embedding_model, vector_store):
    if not text.strip():
        print("System: Tidak ada teks untuk diproses.")
        return
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_text(text)
    
    if not chunks:
        print("System: Tidak ada chunk yang dihasilkan dari teks.")
        return
    
    try:
        embeddings = embedding_model.embed_documents(chunks)
        vector_store.add_texts(texts=chunks, embeddings=embeddings)
        vector_store.save_local(VECTOR_DB_PATH)
        print(f"System: Menyimpan {len(chunks)} chunk ke vector store.")
    except Exception as e:
        print(f"System: Gagal menyimpan ke vector store: {str(e)}")