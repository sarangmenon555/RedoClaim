"""Documents API - upload, OCR processing, clause extraction."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import os
import re
import uuid
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Document, DocumentType, InsuranceType
from app.services.storage.minio_service import upload_file, get_file_url
from app.services.documents.quality_check import check_image_quality, check_pdf_quality
from app.api.deps.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Upload hardening ──────────────────────────────────────────────────────────

# Magic-byte signatures for the file types we claim to accept. The client's
# `Content-Type` header is attacker-controlled (it's just a form field), so
# it is only used as a fast pre-check — this is what actually decides
# whether a file gets treated as one of our allowed types.
_FILE_SIGNATURES = {
    "application/pdf": [b"%PDF-"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/tiff": [b"II*\x00", b"MM\x00*"],
    "image/webp": [b"RIFF"],  # followed by size + "WEBP"; checked specially below
}


def _sniff_content_type(file_bytes: bytes) -> Optional[str]:
    """Identify the file's real type from its magic bytes, or None if unrecognized."""
    for mime, signatures in _FILE_SIGNATURES.items():
        for sig in signatures:
            if file_bytes.startswith(sig):
                if mime == "image/webp":
                    if len(file_bytes) >= 12 and file_bytes[8:12] == b"WEBP":
                        return mime
                    continue
                return mime
    return None


def _sanitize_filename(filename: str) -> str:
    """
    Strip any directory components and dangerous characters from a
    user-supplied filename before it becomes part of a storage path.
    The document's storage key is already namespaced by a UUID, so this is
    purely about not letting a crafted filename (e.g. "../../x" or one
    containing null bytes/control chars) escape the intended prefix or
    cause issues downstream (headers, filesystems, logs).
    """
    name = os.path.basename(filename or "upload")
    name = name.replace("\x00", "")
    name = re.sub(r"[^A-Za-z0-9._\- ]", "_", name)
    name = name.strip(". ") or "upload"
    return name[:200]


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: DocumentType = DocumentType.POLICY,
    insurance_type: Optional[InsuranceType] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Upload an insurance document (policy PDF, rejection letter, etc.).
    Triggers async OCR + embedding pipeline via Celery.
    """
    if file.size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB")

    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"File type not allowed: {file.content_type}")

    file_bytes = await file.read()

    # The declared Content-Type is client-supplied and easily spoofed (it's
    # just a form field) — confirm the bytes actually match one of our
    # allowed types before we trust it for OCR/storage/display.
    sniffed_type = _sniff_content_type(file_bytes)
    if sniffed_type is None or sniffed_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(400, "File content does not match an allowed document type")
    content_type = sniffed_type

    safe_filename = _sanitize_filename(file.filename)
    file_id = str(uuid.uuid4())
    minio_path = f"users/{current_user.id}/documents/{file_id}/{safe_filename}"

    # Pre-OCR quality check — local, instant, no API cost. Catches a bad
    # upload (blurry photo, unreadable PDF) before it wastes an LLM pass
    # and before the user acts on a confidently-wrong analysis.
    page_count = 1
    if content_type == "application/pdf":
        quality = check_pdf_quality(file_bytes)
        page_count = quality.get("page_count", 1) or 1
    else:
        quality = check_image_quality(file_bytes)
    quality_ok = quality["ok"]
    quality_issues = quality["issues"]

    # Upload to MinIO
    try:
        await upload_file(
            bucket=settings.MINIO_BUCKET_DOCUMENTS,
            path=minio_path,
            data=file_bytes,
            content_type=content_type,
        )
    except Exception as e:
        logger.error(f"MinIO upload failed: {e}")
        raise HTTPException(500, "File storage error")

    # Create DB record
    doc = Document(
        id=file_id,
        owner_id=current_user.id,
        file_name=safe_filename,
        file_path=minio_path,
        file_size=len(file_bytes),
        mime_type=content_type,
        doc_type=doc_type,
        insurance_type=insurance_type,
        ocr_status="pending",
        quality_ok=quality_ok,
        quality_issues=quality_issues,
    )
    db.add(doc)
    await db.flush()

    # Queue async processing on Celery — a worker crash or redeploy no
    # longer silently drops in-flight uploads the way FastAPI's
    # BackgroundTasks did (those ran in-process and had no retry/persistence).
    from app.workers.tasks import process_document
    process_document.delay(
        document_id=str(doc.id),
        file_path=minio_path,
        mime_type=content_type,
        doc_type=doc_type.value,
        page_count=page_count,
    )

    return {
        "document_id": str(doc.id),
        "file_name": safe_filename,
        "status": "uploaded",
        "message": "Document uploaded. OCR processing started in background.",
        "quality_ok": quality_ok,
        "quality_issues": quality_issues,
    }


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get document details and analysis results."""
    doc = await db.get(Document, document_id)
    if not doc or str(doc.owner_id) != str(current_user.id):
        raise HTTPException(404, "Document not found")

    return {
        "id": str(doc.id),
        "file_name": doc.file_name,
        "doc_type": doc.doc_type,
        "insurance_type": doc.insurance_type,
        "ocr_status": doc.ocr_status,
        "embedding_status": doc.embedding_status,
        "ocr_text": doc.ocr_text,             # ← included so frontend can check
        "extracted_clauses": doc.extracted_clauses,
        "risk_flags": doc.risk_flags,
        "summary": doc.summary,
        "quality_ok": doc.quality_ok,
        "quality_issues": doc.quality_issues,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.get("/")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all documents for the current user."""
    result = await db.execute(
        select(Document)
        .where(Document.owner_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "file_name": d.file_name,
            "doc_type": d.doc_type,
            "insurance_type": d.insurance_type,
            "ocr_status": d.ocr_status,
            "embedding_status": d.embedding_status,
            "summary": d.summary,
            "quality_ok": d.quality_ok,
            "quality_issues": d.quality_issues,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]