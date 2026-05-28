"""Timeline and Claims API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.models import Claim, ClaimStatus
from app.api.deps.auth import get_current_user

# ─── CLAIMS ROUTER ────────────────────────────────────────────────
router = APIRouter()


@router.get("/")
async def list_claims(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Claim)
        .where(Claim.owner_id == current_user.id)
        .order_by(Claim.created_at.desc())
    )
    claims = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "policy_number": c.policy_number,
            "insurer_name": c.insurer_name,
            "claim_amount": c.claim_amount,
            "insurance_type": c.insurance_type,
            "status": c.status,
            "irdai_violation": c.irdai_violation,
            "audit_report": c.audit_report,
            "claim_date": c.claim_date.isoformat() if c.claim_date else None,
            "rejection_date": c.rejection_date.isoformat() if c.rejection_date else None,
            "gro_deadline": c.gro_deadline.isoformat() if c.gro_deadline else None,
            "irdai_deadline": c.irdai_deadline.isoformat() if c.irdai_deadline else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in claims
    ]


@router.get("/{claim_id}")
async def get_claim(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    claim = await db.get(Claim, claim_id)
    if not claim or str(claim.owner_id) != str(current_user.id):
        raise HTTPException(404, "Claim not found")
    return {
        "id": str(claim.id),
        "policy_number": claim.policy_number,
        "insurer_name": claim.insurer_name,
        "claim_amount": claim.claim_amount,
        "insurance_type": claim.insurance_type,
        "status": claim.status,
        "rejection_reason_raw": claim.rejection_reason_raw,
        "irdai_violation": claim.irdai_violation,
        "irdai_violation_details": claim.irdai_violation_details,
        "audit_report": claim.audit_report,
        "claim_date": claim.claim_date.isoformat() if claim.claim_date else None,
        "rejection_date": claim.rejection_date.isoformat() if claim.rejection_date else None,
        "gro_deadline": claim.gro_deadline.isoformat() if claim.gro_deadline else None,
        "irdai_deadline": claim.irdai_deadline.isoformat() if claim.irdai_deadline else None,
        "created_at": claim.created_at.isoformat() if claim.created_at else None,
    }


@router.put("/{claim_id}/status")
async def update_claim_status(
    claim_id: str,
    status: ClaimStatus,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    claim = await db.get(Claim, claim_id)
    if not claim or str(claim.owner_id) != str(current_user.id):
        raise HTTPException(404, "Claim not found")
    claim.status = status
    await db.commit()
    return {"status": "updated", "new_status": status}
