"""
OCR Pipeline for Indian Insurance Documents.
Supports: PDF, scanned images, hospital bills, discharge summaries.
Primary: PaddleOCR (better for mixed Hindi/English docs) — disabled by default on cloud
Fallback: Tesseract
"""
import io
import os
import logging
from typing import Optional
import pdfplumber
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

PADDLEOCR_ENABLED = os.getenv("PADDLEOCR_ENABLED", "false").lower() == "true"

_paddle_ocr = None


def get_paddle_ocr():
    global _paddle_ocr
    if not PADDLEOCR_ENABLED:
        return None
    if _paddle_ocr is None:
        try:
            from paddleocr import PaddleOCR
            _paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang="en",
                use_gpu=False,
                show_log=False,
            )
            logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            logger.warning(f"PaddleOCR not available, using Tesseract only: {e}")
    return _paddle_ocr


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF.
    - First tries direct text extraction (faster, more accurate for digital PDFs)
    - Falls back to OCR for scanned/image PDFs
    """
    text_parts = []

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):

                page_text = page.extract_text()
                if page_text and len(page_text.strip()) > 50:
                    text_parts.append(page_text)
                else:

                    logger.info(f"Page {page_num+1} appears scanned, using OCR")
                    img = page.to_image(resolution=200).original
                    ocr_text = _ocr_image(img)
                    if ocr_text:
                        text_parts.append(ocr_text)

        full_text = "\n\n".join(text_parts)
        return clean_extracted_text(full_text)

    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise


def extract_text_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Extract text from an uploaded image using OCR."""
    img = Image.open(io.BytesIO(image_bytes))
    return _ocr_image(img)


def _ocr_image(img: Image.Image) -> str:
    """Run OCR on a PIL Image. PaddleOCR first (if enabled), Tesseract fallback."""
    paddle = get_paddle_ocr()

    if paddle:
        try:
            import numpy as np
            img_array = np.array(img.convert("RGB"))
            result = paddle.ocr(img_array, cls=True)
            if result and result[0]:
                lines = [line[1][0] for block in result for line in block if line[1][0]]
                return "\n".join(lines)
        except Exception as e:
            logger.warning(f"PaddleOCR failed: {e}, falling back to Tesseract")

    try:
        text = pytesseract.image_to_string(
            img,
            lang="eng+hin", 
            config="--oem 3 --psm 6",
        )
        return text
    except Exception as e:
        logger.error(f"Tesseract also failed: {e}")
        return ""


def clean_extracted_text(text: str) -> str:
    """Clean and normalize extracted text."""
    import re

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    text = text.replace("Rs.", "Rs. ")
    text = text.replace("₹", "Rs. ")
    text = text.strip()
    return text


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[dict]:
    """
    Split text into overlapping chunks for RAG.
    Returns list of {text, chunk_index, char_start, char_end}
    """
    chunks = []
    start = 0
    idx = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            last_period = text.rfind(".", start, end)
            last_newline = text.rfind("\n", start, end)
            break_point = max(last_period, last_newline)
            if break_point > start + chunk_size // 2:
                end = break_point + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append({
                "text": chunk,
                "chunk_index": idx,
                "char_start": start,
                "char_end": end,
            })
            idx += 1

        start = end - overlap

    return chunks