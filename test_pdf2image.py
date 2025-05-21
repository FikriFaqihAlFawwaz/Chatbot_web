from pdf2image import convert_from_path
try:
    images = convert_from_path("fileujicoba-pdf-png-docx-jpeg-jpg/dasarpemrogramanpython.pdf")
    print(f"Berhasil mengonversi {len(images)} halaman.")
except Exception as e:
    print(f"Error: {str(e)}")