import pytesseract
import cv2
import os
import numpy as np
from typing import Optional
import logging

logging.getLogger("pytesseract").setLevel(logging.WARNING)
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

def preprocess_image(image: np.ndarray) -> np.ndarray:
    if image is None:
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    processed_img = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
    )
    return processed_img

def extract_text_from_image(image_path: str) -> str:
    if not os.path.exists(image_path):
        return f"❌ Error: File gambar '{image_path}' tidak ditemukan."
    image = cv2.imread(image_path)
    if image is None:
        return "❌ Error: Tidak dapat membaca gambar."
    height, width = image.shape[:2]
    if height < 100 or width < 100:
        return "⚠️ Gambar memiliki resolusi terlalu rendah untuk mengekstrak teks."
    processed_img = preprocess_image(image)
    text = pytesseract.image_to_string(processed_img, lang="eng+ind")
    return text.strip() or "⚠️ Tidak ada teks yang terdeteksi dalam gambar. Coba gunakan gambar dengan teks yang lebih jelas."

def extract_text(file_path: str) -> Optional[str]:
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".heic", ".svg"]:
        return f"❌ Error: Format file '{ext}' tidak didukung."
    return extract_text_from_image(file_path)