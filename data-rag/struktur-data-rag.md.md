/data-rag/                  # Folder untuk RAG System (Chat Dokumen)
    ├── documents/         # Subfolder untuk dokumen
    │   ├── pdf/           # Untuk file PDF
    │   ├── doc/           # Untuk file DOC
    │   ├── docx/          # Untuk file DOCX
    │   ├── odt/           # Untuk file ODT
    │   ├── txt/           # Untuk file TXT
    ├── embeddings/        # Folder untuk menyimpan vektor embedding
    ├── faiss_index/       # Folder penyimpanan FAISS Index
    │   ├── index.faiss
    │   └── index.pkl
    └── logs/              # Log untuk RAG System
        └── archive/