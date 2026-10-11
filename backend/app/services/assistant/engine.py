import logging
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.middleware import sanitize_user_input
from app.models.models import Claim, Document
from app.services.assistant.composer import compose_answer
from app.services.assistant.context import Ctx
from app.services.assistant.doc_classifier import KIND_LABELS, kind_of_document
from app.services.assistant.params import clean_params
from app.services.assistant.planner import build_plan
from app.services.assistant.tools import EXECUTORS

logger = logging.getLogger(__name__)

MAX_DOCS = 8

SUGGESTIONS = {
    "draft_appeal": ("Draft my appeal letter", "Please draft the appeal letter for this claim"),
    "cost_benefit": ("Is it worth pursuing?", "Help me decide whether it is worth pursuing this claim"),
    "precedents": ("Show similar past cases", "Show me similar past cases"),
    "estimate_payout": ("Estimate what my policy may pay", "Estimate what my policy may pay for my claim"),
    "waiting_period": ("Check my waiting periods", "Check my waiting periods"),
    "ejagriti_guide": ("How do I file on e-Jagriti?", "How do I file a complaint on e-Jagriti?"),
    "next_steps": ("What are my next steps?", "What are my next steps and deadlines?"),
}


def _is_uuid(value) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


async def load_documents(db: AsyncSession, user, ids: list) -> list:
    docs = []
    seen = set()
    for raw in ids[:MAX_DOCS]:
        if not _is_uuid(raw) or str(raw) in seen:
            continue
        seen.add(str(raw))
        doc = await db.get(Document, str(raw))
        if doc is None or str(doc.owner_id) != str(user.id):
            continue
        docs.append(doc)
    if any(d.ocr_status in ("pending", "processing") for d in docs):
        raise HTTPException(409, "Your documents are still being read. Please try again in a few seconds.")
    return [d for d in docs if d.ocr_status == "done" and (d.ocr_text or "").strip()]


def _suggest(results: dict, order: list) -> list:
    ran = set(order)
    picks = []
    audit = results.get("audit_rejection")
    if audit and audit["status"] == "ok":
        picks += [k for k in ("draft_appeal", "cost_benefit", "precedents") if k not in ran]
    elif "draft_appeal" in ran and results.get("draft_appeal", {}).get("status") == "ok":
        picks += ["next_steps", "ejagriti_guide"]
    elif results.get("analyze_policy", {}).get("status") == "ok":
        picks += [k for k in ("estimate_payout", "waiting_period") if k not in ran]
    return [
        {"id": key, "label": SUGGESTIONS[key][0], "message": SUGGESTIONS[key][1]}
        for key in picks[:3]
    ]


async def handle_message(
    db: AsyncSession, user, lang: str, message: str, document_ids: list,
    new_document_ids: list, context: dict, history: list,
) -> dict:
    text = sanitize_user_input(message, 4000)
    if not text and not new_document_ids:
        raise HTTPException(400, "Please type your question or attach a document.")
    if not text:
        text = "Please review the document I attached."

    docs = await load_documents(db, user, document_ids)
    kinds = {str(d.id): kind_of_document(d) for d in docs}

    claim_id = context.get("claim_id") if isinstance(context, dict) else None
    if claim_id and _is_uuid(claim_id):
        claim = await db.get(Claim, str(claim_id))
        claim_id = str(claim.id) if claim is not None and str(claim.owner_id) == str(user.id) else None
    else:
        claim_id = None

    ctx = Ctx(
        db=db, user=user, message=text, docs=docs, kinds=kinds,
        params=clean_params((context or {}).get("params")), claim_id=claim_id,
        history=[h for h in (history or []) if isinstance(h, dict)][-8:],
        new_doc_ids={str(i) for i in new_document_ids if _is_uuid(i)},
    )

    pending = (context or {}).get("pending") or []
    order = await build_plan(ctx, pending if isinstance(pending, list) else [])

    for name in order:
        try:
            ctx.results[name] = await EXECUTORS[name](ctx)
        except Exception as exc:
            logger.error(f"Assistant tool {name} crashed: {exc}", exc_info=True)
            ctx.results[name] = {"status": "error", "label": name, "message": "Something went wrong while running this check.", "highlights": [], "data": {}, "links": []}

    answer = await compose_answer(ctx, ctx.results, order)

    if lang != "en":
        try:
            from app.services.language.sarvam_service import sarvam_client
            if sarvam_client.enabled:
                answer = await sarvam_client.translate_long_text(answer, lang)
        except Exception as exc:
            logger.error(f"Assistant translation failed, returning English: {exc}")

    new_pending = [
        {"intent": n, "missing": [f["key"] for f in ctx.results[n].get("fields", [])]}
        for n in order if ctx.results[n]["status"] == "needs_input"
    ]
    needs = [
        {"intent": n, "label": ctx.results[n]["label"], "question": ctx.results[n].get("question"), "fields": ctx.results[n].get("fields", [])}
        for n in order if ctx.results[n]["status"] == "needs_input"
    ]
    modules = [
        {
            "id": n, "label": ctx.results[n]["label"], "status": ctx.results[n]["status"],
            "highlights": ctx.results[n].get("highlights", []), "data": ctx.results[n].get("data", {}),
            "links": ctx.results[n].get("links", []), "message": ctx.results[n].get("message"),
        }
        for n in order if ctx.results[n]["status"] != "needs_input"
    ]

    return {
        "answer": answer,
        "language": lang,
        "modules": modules,
        "needs": needs,
        "suggestions": _suggest(ctx.results, order),
        "documents": [{"id": str(d.id), "file_name": d.file_name, "kind": kinds[str(d.id)], "label": KIND_LABELS.get(kinds[str(d.id)], "Document")} for d in docs],
        "context": {"params": ctx.params, "claim_id": ctx.claim_id, "pending": new_pending},
    }
