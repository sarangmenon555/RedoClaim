"""
Document quality check — runs before the OCR/LLM pipeline (and again after
OCR) to catch upload problems that would otherwise silently produce a
confident-looking but wrong AI analysis: blurry photos, low-resolution
scans, missing pages, or a page that OCR simply couldn't read.

Entirely local (OpenCV/Pillow/pdfplumber, all already in requirements.txt)
— no external API calls, no added cost per upload.
"""
import io
import logging
import numpy as np
import cv2
from PIL import Image

logger = logging.getLogger(__name__)

BLUR_THRESHOLD = 100.0        # Laplacian variance below this = likely blurry
MIN_DIMENSION_PX = 600        # shorter side below this = too low-res to OCR reliably
LOW_TEXT_CHARS_PER_PAGE = 40  # avg extracted chars/page below this = likely blank/missing content
PDF_SAMPLE_PAGES = 5          # only rasterize first N pages for blur check — keep uploads fast


def _blur_score(img: Image.Image) -> float:
    gray = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def check_image_quality(image_bytes: bytes) -> dict:
    """Run on a JPEG/PNG/etc. upload before OCR. Returns {ok, issues}."""
    issues = []
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size

        if min(width, height) < MIN_DIMENSION_PX:
            issues.append(
                f"Image resolution is low ({width}x{height}px) — text may not be readable. "
                "Try a higher-resolution photo or scan."
            )

        score = _blur_score(img)
        if score < BLUR_THRESHOLD:
            issues.append(
                f"Image appears blurry (sharpness score {score:.0f}, ideally 100+). "
                "Consider retaking the photo with better lighting and a steadier hand."
            )

    except Exception as e:
        logger.warning(f"Quality check failed to open image: {e}")
        issues.append("Could not read this image file — it may be corrupted or an unsupported format.")

    return {"ok": len(issues) == 0, "issues": issues}


def check_pdf_quality(pdf_bytes: bytes) -> dict:
    """Run on a PDF upload before OCR. Returns {ok, issues, page_count}."""
    issues = []
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page_count = len(pdf.pages)
            if page_count == 0:
                return {"ok": False, "issues": ["This PDF has no pages."], "page_count": 0}

            blurry_pages = 0
            sampled = pdf.pages[:PDF_SAMPLE_PAGES]
            for page in sampled:
                try:
                    img = page.to_image(resolution=150).original
                    if _blur_score(img) < BLUR_THRESHOLD:
                        blurry_pages += 1
                except Exception as page_err:
                    logger.warning(f"Could not rasterize a page for quality check: {page_err}")

            if blurry_pages > 0:
                issues.append(
                    f"{blurry_pages} of the first {len(sampled)} page(s) look like blurry or low-quality "
                    "scans — some content may not extract correctly."
                )

        return {"ok": len(issues) == 0, "issues": issues, "page_count": page_count}

    except Exception as e:
        logger.warning(f"Quality check failed to open PDF: {e}")
        return {
            "ok": False,
            "issues": ["Could not read this PDF — it may be corrupted, empty, or password-protected."],
            "page_count": 0,
        }


def check_extracted_text(text: str, page_count: int = 1) -> dict:
    """
    Post-OCR sanity check: catches the case where the file itself looked fine
    but OCR still came back nearly empty (blank scan, unreadable handwriting,
    an OCR engine failure that didn't raise an exception).
    """
    issues = []
    if not text or not text.strip():
        issues.append(
            "No text could be extracted from this document. It may be blank, a low-quality scan, "
            "or in a format this tool couldn't read — please check the file and try re-uploading."
        )
    else:
        chars_per_page = len(text.strip()) / max(page_count, 1)
        if chars_per_page < LOW_TEXT_CHARS_PER_PAGE:
            issues.append(
                "Very little text was extracted relative to the document's length — some pages or "
                "sections may be missing from the analysis below."
            )
    return {"ok": len(issues) == 0, "issues": issues}
