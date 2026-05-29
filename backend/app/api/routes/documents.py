"""Documents API - upload, OCR processing, clause extraction."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
import logging

from app.core.database import get_db, AsyncSessionLocal   # ← FIXED: moved from bottom
from app.core.config import settings
from app.models.models import Document, DocumentType, InsuranceType
from app.services.ocr.ocr_pipeline import (
    extract_text_from_pdf, extract_text_from_image, chunk_text
)
from app.services.rag.rag_pipeline import upsert_document_chunks
from app.services.llm.gemini_service import extract_policy_clauses
from app.services.storage.minio_service import upload_file, get_file_url
from app.api.deps.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: DocumentType = DocumentType.POLICY,
    insurance_type: Optional[InsuranceType] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Upload an insurance document (policy PDF, rejection letter, etc.).
    Triggers async OCR + embedding pipeline.
    """
    if file.size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB")

    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"File type not allowed: {file.content_type}")

    file_bytes = await file.read()
    file_id = str(uuid.uuid4())
    minio_path = f"users/{current_user.id}/documents/{file_id}/{file.filename}"

    # Upload to MinIO
    try:
        await upload_file(
            bucket=settings.MINIO_BUCKET_DOCUMENTS,
            path=minio_path,
            data=file_bytes,
            content_type=file.content_type,
        )
    except Exception as e:
        logger.error(f"MinIO upload failed: {e}")
        raise HTTPException(500, "File storage error")

    # Create DB record
    doc = Document(
        id=file_id,
        owner_id=current_user.id,
        file_name=file.filename,
        file_path=minio_path,
        file_size=len(file_bytes),
        mime_type=file.content_type,
        doc_type=doc_type,
        insurance_type=insurance_type,
        ocr_status="pending",
    )
    db.add(doc)
    await db.flush()

    # Queue async processing
    background_tasks.add_task(
        process_document_async,
        str(doc.id),
        file_bytes,
        file.content_type,
        doc_type,
    )

    return {
        "document_id": str(doc.id),
        "file_name": file.filename,
        "status": "uploaded",
        "message": "Document uploaded. OCR processing started in background.",
    }


async def process_document_async(
    doc_id: str,
    file_bytes: bytes,
    mime_type: str,
    doc_type: DocumentType,
):
    """Background task: OCR → chunk → embed → (for policies) extract clauses."""
    async with AsyncSessionLocal() as db:
        doc = None
        try:
            doc = await db.get(Document, doc_id)
            if not doc:
                logger.error(f"Background task: document {doc_id} not found in DB")
                return

            # Step 1: OCR
            doc.ocr_status = "processing"
            await db.commit()

            if mime_type == "application/pdf":
                text = extract_text_from_pdf(file_bytes)
            else:
                text = extract_text_from_image(file_bytes, mime_type)

            logger.info(f"OCR complete for {doc_id}: {len(text)} chars extracted")

            if not text or len(text.strip()) < 20:
                logger.warning(f"OCR returned very little text for {doc_id} — possible scanned/image PDF")

            doc.ocr_text = text
            doc.ocr_status = "done"

            # Step 2: Chunk + embed
            chunks = chunk_text(text)
            await upsert_document_chunks(
                document_id=doc_id,
                user_id=str(doc.owner_id),
                chunks=chunks,
            )
            doc.embedding_status = "done"

            # Step 3: For policies, extract clauses
            if doc_type == DocumentType.POLICY and text:
                clauses = await extract_policy_clauses(text)
                doc.extracted_clauses = clauses
                doc.summary = clauses.get("plain_english_summary", "")
                doc.risk_flags = clauses.get("risky_clauses", [])

            await db.commit()
            logger.info(f"Document {doc_id} processing complete")

        except Exception as e:
            logger.error(f"Document processing failed for {doc_id}: {e}", exc_info=True)
            try:
                if doc:
                    doc.ocr_status = "failed"
                    await db.commit()
            except Exception as commit_err:
                logger.error(f"Failed to mark {doc_id} as failed: {commit_err}")


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
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]