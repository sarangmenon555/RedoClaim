"""Celery task definitions."""
from app.workers.celery_app import celery_app
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run async code inside a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: str, file_path: str, mime_type: str, doc_type: str):
    """Process uploaded document: OCR → chunk → embed → extract clauses."""
    try:
        from app.services.storage.minio_service import download_file
        from app.services.ocr.ocr_pipeline import (
            extract_text_from_pdf, extract_text_from_image, chunk_text
        )
        from app.services.rag.rag_pipeline import upsert_document_chunks
        from app.services.llm.gemini_service import extract_policy_clauses
        from app.core.database import AsyncSessionLocal
        from app.models.models import Document, DocumentType

        async def _run():
            file_bytes = await download_file("redoclaim-documents", file_path)

            if mime_type == "application/pdf":
                text = extract_text_from_pdf(file_bytes)
            else:
                text = extract_text_from_image(file_bytes, mime_type)

            async with AsyncSessionLocal() as db:
                doc = await db.get(Document, document_id)
                if not doc:
                    return

                doc.ocr_text = text
                doc.ocr_status = "done"
                await db.commit()

                chunks = chunk_text(text)
                await upsert_document_chunks(
                    document_id=document_id,
                    user_id=str(doc.owner_id),
                    chunks=chunks,
                )
                doc.embedding_status = "done"

                if doc_type == DocumentType.POLICY.value and text:
                    clauses = await extract_policy_clauses(text)
                    doc.extracted_clauses = clauses
                    doc.summary = clauses.get("plain_english_summary", "")
                    doc.risk_flags = clauses.get("risky_clauses", [])

                await db.commit()
                logger.info(f"Document {document_id} processed successfully")

        run_async(_run())

    except Exception as exc:
        logger.error(f"Document processing failed: {exc}")
        self.retry(exc=exc)


@celery_app.task
def send_deadline_reminders():
    """
    Daily job: check IRDAI grievance deadlines and flag urgent cases.
    Runs at 9 AM IST every day.
    """
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.models import Claim
        from sqlalchemy import select
        from datetime import timedelta

        now = datetime.now()
        warning_window = now + timedelta(days=3)  # Warn 3 days before deadline

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Claim).where(
                    Claim.gro_deadline.isnot(None),
                    Claim.gro_deadline <= warning_window,
                    Claim.gro_reminder_sent == False,
                )
            )
            urgent_claims = result.scalars().all()

            for claim in urgent_claims:
                days_left = (claim.gro_deadline - now).days
                logger.warning(
                    f"URGENT: Claim {claim.id} GRO deadline in {days_left} days! "
                    f"User: {claim.owner_id}"
                )
                claim.gro_reminder_sent = True

            await db.commit()
            logger.info(f"Deadline check: {len(urgent_claims)} urgent claims flagged")

    run_async(_run())


@celery_app.task(bind=True, max_retries=2)
def generate_appeal_task(self, claim_id: str, appeal_type: str, user_id: str):
    """Background appeal letter generation for large/complex cases."""
    try:
        async def _run():
            from app.core.database import AsyncSessionLocal
            from app.models.models import Claim, Appeal, AppealType
            from app.services.llm.gemini_service import generate_appeal_letter
            import time

            async with AsyncSessionLocal() as db:
                claim = await db.get(Claim, claim_id)
                if not claim:
                    return

                start = time.time()
                letter = await generate_appeal_letter(
                    appeal_type=appeal_type,
                    claim_data={
                        "insurer_name": claim.insurer_name,
                        "policy_number": claim.policy_number,
                        "claim_amount": claim.claim_amount,
                    },
                    audit_report=claim.audit_report.get("audit", {}) if claim.audit_report else {},
                    policy_clauses={},
                    user_name="Policyholder",
                    policy_number=claim.policy_number or "",
                    insurer_name=claim.insurer_name,
                )

                appeal = Appeal(
                    owner_id=user_id,
                    claim_id=claim_id,
                    appeal_type=appeal_type,
                    letter_content=letter,
                    generation_time_ms=int((time.time() - start) * 1000),
                )
                db.add(appeal)
                await db.commit()

        run_async(_run())
    except Exception as exc:
        self.retry(exc=exc)
