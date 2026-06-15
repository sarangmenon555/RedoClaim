"""Appeals API - generate GRO, Ombudsman, Bima Bharosa, Consumer Court letters."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import logging
import time

from app.core.database import get_db
from app.models.models import Claim, Appeal, AppealType
from app.services.llm.gemini_service import generate_appeal_letter
from app.api.deps.auth import get_current_user


AI_DISCLAIMER = {
    "disclaimer": (
        "This letter is an AI-generated DRAFT. It has not been reviewed by a licensed advocate. "
        "Read every line carefully. Verify your name, policy number, dates, and claim amount. "
        "Check all IRDAI regulation citations at irdai.gov.in. Correct any errors before sending. "
        "This is NOT legal advice. For claims above Rs. 10 Lakhs, consult a licensed advocate."
    ),
    "verify_at": "https://www.irdai.gov.in",
    "free_legal_aid": "DLSA (District Legal Services Authority) provides free legal aid",
}


router = APIRouter()
logger = logging.getLogger(__name__)


class AppealGenerateRequest(BaseModel):
    claim_id: str
    appeal_type: AppealType
    additional_context: Optional[str] = None


def _extract_audit_data(audit_report: dict) -> tuple[dict, dict, list]:
    """
    Extract audit result, policy clauses, and violations from the stored report.

    Stored structure:
    {
      "hierarchy_of_evidence": {
        "step1_sla": {...},
        "step2_regulations": {
          "audit": {...},          ← main LLM audit result
          "moratorium": {...},
          "cis_check": {...},
          "deficiency_in_service": {...}
        },
        "step3_redressal": {...}
      },
      "policy_clauses": {...},
      ...
    }
    """
    hoe = audit_report.get("hierarchy_of_evidence", {})
    step2 = hoe.get("step2_regulations", {})
    audit_result = step2.get("audit", {})
    policy_clauses = audit_report.get("policy_clauses", {})

    # Collect all violations: IRDAI + SLA
    irdai_violations = audit_result.get("step2_regulatory_violations", [])
    sla_violations = hoe.get("step1_sla", {}).get("sla_violations", [])

    # Build a combined audit_report dict for the letter generator
    # that includes all the fields it needs at the top level
    combined = {
        **audit_result,
        "step1_sla_analysis": hoe.get("step1_sla", {}),
        "deficiency_statement": step2.get("deficiency_in_service", {}).get("statement", ""),
        "moratorium": step2.get("moratorium", {}),
    }

    all_violations = irdai_violations + [
        {
            "violation": v.get("detail", ""),
            "regulation": v.get("regulation", ""),
            "severity": v.get("severity", "high"),
            "argument": v.get("interest_note", ""),
        }
        for v in sla_violations
    ]

    return combined, policy_clauses, all_violations


@router.post("/generate")
async def generate_appeal(
    req: AppealGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generate a professional appeal letter.
    Types: GRO | Ombudsman | Bima Bharosa | Consumer Court | Insurer Escalation
    """
    claim = await db.get(Claim, req.claim_id)
    if not claim or str(claim.owner_id) != str(current_user.id):
        raise HTTPException(404, "Claim not found")

    if not claim.audit_report:
        raise HTTPException(400, "Run rejection audit first before generating appeal.")

    # Extract audit data from the correct nested path
    audit_result, policy_clauses, all_violations = _extract_audit_data(claim.audit_report)

    start = time.time()
    letter = await generate_appeal_letter(
        appeal_type=req.appeal_type.value,
        claim_data={
            "insurer_name": claim.insurer_name,
            "policy_number": claim.policy_number,
            "claim_amount": claim.claim_amount,
            "insurance_type": claim.insurance_type.value if hasattr(claim.insurance_type, "value") else claim.insurance_type,
            "rejection_reason": claim.rejection_reason_raw or "",
            "rejection_date": claim.rejection_date.isoformat() if claim.rejection_date else "",
            "additional_context": req.additional_context or "",
        },
        audit_report=audit_result,
        policy_clauses=policy_clauses,
        user_name=current_user.full_name,
        policy_number=claim.policy_number or "UNKNOWN",
        insurer_name=claim.insurer_name,
    )
    elapsed = int((time.time() - start) * 1000)

    # Save appeal
    appeal = Appeal(
        owner_id=current_user.id,
        claim_id=req.claim_id,
        appeal_type=req.appeal_type,
        letter_content=letter,
        legal_references=all_violations,
        model_used="groq-llama-3.3-70b",
        generation_time_ms=elapsed,
    )
    db.add(appeal)
    await db.flush()

    return {
        "appeal_id": str(appeal.id),
        "appeal_type": req.appeal_type.value,
        "ai_disclaimer": AI_DISCLAIMER,
        "letter": letter,
        "legal_references": all_violations,
        "generation_time_ms": elapsed,
    }


@router.get("/claim/{claim_id}")
async def list_appeals_for_claim(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all generated appeals for a claim."""
    from sqlalchemy import select
    claim = await db.get(Claim, claim_id)
    if not claim or str(claim.owner_id) != str(current_user.id):
        raise HTTPException(404, "Claim not found")

    result = await db.execute(
        select(Appeal).where(Appeal.claim_id == claim_id).order_by(Appeal.created_at.desc())
    )
    appeals = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "appeal_type": a.appeal_type,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            "response_received": a.response_received,
            "outcome": a.outcome,
        }
        for a in appeals
    ]


@router.get("/{appeal_id}")
async def get_appeal(
    appeal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    appeal = await db.get(Appeal, appeal_id)
    if not appeal or str(appeal.owner_id) != str(current_user.id):
        raise HTTPException(404, "Appeal not found")
    return {
        "id": str(appeal.id),
        "appeal_type": appeal.appeal_type,
        "letter_content": appeal.letter_content,
        "legal_references": appeal.legal_references,
        "created_at": appeal.created_at.isoformat() if appeal.created_at else None,
    }