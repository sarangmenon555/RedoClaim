"""Timeline and Claims API routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import io

from app.core.database import get_db
from app.models.models import Claim, ClaimStatus, Appeal
from app.api.deps.auth import get_current_user
from app.services.documents.pdf_export import build_audit_trail_pdf

# ─── CLAIMS ROUTER ────────────────────────────────────────────────
router = APIRouter()


@router.get("/patients")
async def list_patients(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Distinct patients this account has filed claims for — powers the
    "manage claims for" selector on the frontend. The account holder
    themselves (patient_name is NULL) is always included first.
    """
    result = await db.execute(
        select(Claim.patient_name, Claim.patient_relationship)
        .where(Claim.owner_id == current_user.id)
        .distinct()
    )
    rows = result.all()
    patients = [{"patient_name": None, "patient_relationship": "self", "label": current_user.full_name}]
    seen = set()
    for name, relationship in rows:
        if name and name not in seen:
            seen.add(name)
            patients.append({"patient_name": name, "patient_relationship": relationship, "label": name})
    return patients


@router.get("/")
async def list_claims(
    patient_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = select(Claim).where(Claim.owner_id == current_user.id)
    if patient_name is not None:
        # "" (empty string) explicitly means "the account holder's own claims"
        query = query.where(Claim.patient_name == (patient_name or None))
    result = await db.execute(query.order_by(Claim.created_at.desc()))
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
            "patient_name": c.patient_name,
            "patient_relationship": c.patient_relationship,
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
        "patient_name": claim.patient_name,
        "patient_relationship": claim.patient_relationship,
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


class PatientUpdateRequest(BaseModel):
    patient_name: Optional[str] = None
    patient_relationship: Optional[str] = None


@router.put("/{claim_id}/patient")
async def update_claim_patient(
    claim_id: str,
    req: PatientUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Assign or reassign which family member a claim was filed for."""
    claim = await db.get(Claim, claim_id)
    if not claim or str(claim.owner_id) != str(current_user.id):
        raise HTTPException(404, "Claim not found")
    claim.patient_name = (req.patient_name or "").strip() or None
    claim.patient_relationship = req.patient_relationship
    await db.commit()
    return {"status": "updated", "patient_name": claim.patient_name, "patient_relationship": claim.patient_relationship}


@router.get("/deadlines/urgent")
async def get_urgent_deadlines(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Live view of this user's claims with a GRO/IRDAI deadline in the next 3
    days or already overdue — for an in-app banner/notification, since
    there's no email/SMS channel wired up. Computed fresh on every call
    (doesn't rely on the reminder_sent flags, which are only there to stop
    the backend's daily log job from repeating itself).
    """
    now = datetime.now()
    warning_window = now + timedelta(days=3)

    result = await db.execute(
        select(Claim).where(
            Claim.owner_id == current_user.id,
            Claim.status != ClaimStatus.RESOLVED,
        )
    )
    claims = result.scalars().all()

    urgent = []
    for c in claims:
        for field, label in [("gro_deadline", "GRO response"), ("irdai_deadline", "IRDAI Ombudsman filing")]:
            deadline = getattr(c, field)
            if deadline and deadline <= warning_window:
                urgent.append({
                    "claim_id": str(c.id),
                    "insurer_name": c.insurer_name,
                    "deadline_type": label,
                    "deadline_date": deadline.isoformat(),
                    "days_remaining": (deadline - now).days,
                    "is_overdue": deadline < now,
                })

    urgent.sort(key=lambda d: d["deadline_date"])
    return urgent


@router.get("/{claim_id}/timeline")
async def get_claim_timeline(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Chronological view of everything that's happened on a claim — filing,
    rejection, GRO/appeal filings and their outcomes, and upcoming IRDAI
    deadlines — for the timeline UI. Pure read, built entirely from
    existing Claim/Appeal fields.
    """
    claim = await db.get(Claim, claim_id)
    if not claim or str(claim.owner_id) != str(current_user.id):
        raise HTTPException(404, "Claim not found")

    result = await db.execute(
        select(Appeal).where(Appeal.claim_id == claim_id).order_by(Appeal.created_at.asc())
    )
    appeals = result.scalars().all()

    events = []

    if claim.claim_date:
        events.append({
            "date": claim.claim_date.isoformat(),
            "type": "claim_filed",
            "title": "Claim filed",
            "status": "done",
        })
    if claim.rejection_date:
        events.append({
            "date": claim.rejection_date.isoformat(),
            "type": "claim_rejected",
            "title": f"Claim rejected by {claim.insurer_name}",
            "status": "done",
        })

    for appeal in appeals:
        events.append({
            "date": (appeal.submitted_at or appeal.created_at).isoformat(),
            "type": "appeal_filed",
            "title": f"{appeal.appeal_type.value.replace('_', ' ').title()} filed",
            "status": "done" if appeal.submitted_at else "drafted",
            "appeal_id": str(appeal.id),
        })
        if appeal.outcome and appeal.outcome != "pending":
            events.append({
                "date": (appeal.submitted_at or appeal.created_at).isoformat(),
                "type": "appeal_outcome",
                "title": f"{appeal.appeal_type.value.replace('_', ' ').title()} outcome: {appeal.outcome}",
                "status": appeal.outcome,
                "appeal_id": str(appeal.id),
            })

    now = datetime.now(claim.created_at.tzinfo) if claim.created_at and claim.created_at.tzinfo else datetime.now()

    upcoming = []
    if claim.gro_deadline and claim.status not in (ClaimStatus.RESOLVED,):
        upcoming.append({
            "date": claim.gro_deadline.isoformat(),
            "type": "gro_deadline",
            "title": "GRO response deadline",
            "is_overdue": claim.gro_deadline < now,
            "days_remaining": (claim.gro_deadline - now).days,
        })
    if claim.irdai_deadline and claim.status not in (ClaimStatus.RESOLVED,):
        upcoming.append({
            "date": claim.irdai_deadline.isoformat(),
            "type": "irdai_deadline",
            "title": "IRDAI Ombudsman filing deadline",
            "is_overdue": claim.irdai_deadline < now,
            "days_remaining": (claim.irdai_deadline - now).days,
        })

    events.sort(key=lambda e: e["date"])

    return {
        "claim_id": str(claim.id),
        "current_status": claim.status,
        "events": events,
        "upcoming_deadlines": upcoming,
    }


@router.get("/{claim_id}/export-pdf")
async def export_claim_pdf(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Bundle this claim's summary, audit findings, appeal letters, and
    timeline into one downloadable PDF — built with ReportLab (free,
    open-source), no new API cost per export.
    """
    claim = await db.get(Claim, claim_id)
    if not claim or str(claim.owner_id) != str(current_user.id):
        raise HTTPException(404, "Claim not found")

    result = await db.execute(
        select(Appeal).where(Appeal.claim_id == claim_id).order_by(Appeal.created_at.asc())
    )
    appeals = result.scalars().all()

    # Reuse the same event-building logic as the timeline endpoint so the
    # PDF and the in-app timeline never drift apart.
    timeline_resp = await get_claim_timeline(claim_id, db=db, current_user=current_user)

    claim_dict = {
        "insurer_name": claim.insurer_name,
        "policy_number": claim.policy_number,
        "insurance_type": claim.insurance_type.value if hasattr(claim.insurance_type, "value") else claim.insurance_type,
        "claim_amount": claim.claim_amount,
        "patient_name": claim.patient_name,
        "status": claim.status.value if hasattr(claim.status, "value") else claim.status,
        "claim_date": claim.claim_date.strftime("%d %b %Y") if claim.claim_date else None,
        "rejection_date": claim.rejection_date.strftime("%d %b %Y") if claim.rejection_date else None,
        "gro_deadline": claim.gro_deadline.strftime("%d %b %Y") if claim.gro_deadline else None,
        "irdai_deadline": claim.irdai_deadline.strftime("%d %b %Y") if claim.irdai_deadline else None,
        "rejection_reason_raw": claim.rejection_reason_raw,
    }

    appeals_data = [
        {
            "appeal_type": a.appeal_type.value if hasattr(a.appeal_type, "value") else a.appeal_type,
            "letter_content": a.letter_content,
            "submitted_at": a.submitted_at.strftime("%d %b %Y") if a.submitted_at else None,
            "outcome": a.outcome,
        }
        for a in appeals
    ]

    pdf_bytes = build_audit_trail_pdf(
        user_name=current_user.full_name,
        claim=claim_dict,
        audit_report=claim.audit_report,
        appeals=appeals_data,
        timeline_events=timeline_resp["events"],
    )

    filename = f"redoclaim-audit-trail-{claim.policy_number or claim_id[:8]}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
