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
def process_document(
    self,
    document_id: str,
    file_path: str,
    mime_type: str,
    doc_type: str,
    page_count: int = 1,
):
    """Process uploaded document: OCR → sanitize → chunk → embed → extract clauses."""
    try:
        from app.services.storage.minio_service import download_file
        from app.services.ocr.ocr_pipeline import (
            extract_text_from_pdf, extract_text_from_image, chunk_text
        )
        from app.services.rag.rag_pipeline import upsert_document_chunks
        from app.services.llm.gemini_service import extract_policy_clauses
        from app.services.documents.quality_check import check_extracted_text
        from app.core.middleware import sanitize_user_input, check_prompt_injection
        from app.core.database import AsyncSessionLocal
        from app.models.models import Document, DocumentType

        async def _run():
            file_bytes = await download_file("redoclaim-documents", file_path)

            doc_status = "processing"
            async with AsyncSessionLocal() as db:
                doc = await db.get(Document, document_id)
                if not doc:
                    logger.error(f"process_document: document {document_id} not found")
                    return
                doc.ocr_status = doc_status
                await db.commit()

            if mime_type == "application/pdf":
                text = extract_text_from_pdf(file_bytes)
            else:
                text = extract_text_from_image(file_bytes, mime_type)

            logger.info(f"OCR complete for {document_id}: {len(text or '')} chars extracted")

            # Documents are user-uploaded content that gets fed straight into
            # LLM prompts downstream (clause extraction, audits, appeal
            # letters). Sanitize it and flag — but don't block on — anything
            # that looks like a prompt-injection attempt, since we still
            # want to process the user's own real document.
            text = sanitize_user_input(text or "", max_length=200_000)
            injection_detected = check_prompt_injection(text) if text else False
            if injection_detected:
                logger.warning(f"Possible prompt-injection pattern detected in document {document_id}")

            async with AsyncSessionLocal() as db:
                doc = await db.get(Document, document_id)
                if not doc:
                    return

                doc.ocr_text = text
                doc.ocr_status = "done"

                # Post-OCR quality check — catches a file that looked fine on
                # upload but OCR still returned little/no usable text.
                post_ocr_quality = check_extracted_text(text, page_count=page_count)
                issues = list(doc.quality_issues or [])
                if not post_ocr_quality["ok"]:
                    issues += post_ocr_quality["issues"]
                    doc.quality_ok = False
                if injection_detected:
                    issues.append("Unusual instruction-like text detected in document — reviewed with extra caution.")
                doc.quality_issues = issues

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
        logger.error(f"Document processing failed for {document_id}: {exc}", exc_info=True)
        try:
            async def _mark_failed():
                async with AsyncSessionLocal() as db:
                    doc = await db.get(Document, document_id)
                    if doc:
                        doc.ocr_status = "failed"
                        await db.commit()
            run_async(_mark_failed())
        except Exception as mark_err:
            logger.error(f"Failed to mark {document_id} as failed: {mark_err}")
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
