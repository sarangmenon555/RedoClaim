"""
Network Hospital Verifier — crowdsourced. Insurers frequently change their
cashless hospital networks, and "hospital was delisted" is a common
cashless-denial reason. There's no paid hospital-network API wired up here,
so this starts as a user-contributed database: anyone can report a
hospital's status for a given insurer, and the most recent report for an
insurer+hospital pair is what's shown (with its date, so the user can judge
how current it is).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
import uuid

from app.core.database import get_db
from app.models.models import NetworkHospital, HospitalNetworkStatus
from app.api.deps.auth import get_current_user

router = APIRouter()


class HospitalReportRequest(BaseModel):
    insurer_name: str
    hospital_name: str
    city: Optional[str] = None
    status: HospitalNetworkStatus
    note: Optional[str] = None


@router.post("/report")
async def report_hospital_status(
    body: HospitalReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Submit a crowdsourced report of a hospital's cashless-network status for an insurer."""
    entry = NetworkHospital(
        id=uuid.uuid4(),
        insurer_name=body.insurer_name.strip(),
        hospital_name=body.hospital_name.strip(),
        city=(body.city or "").strip() or None,
        status=body.status,
        reported_by_id=current_user.id,
        note=(body.note or "").strip() or None,
    )
    db.add(entry)
    await db.commit()
    return {"status": "recorded", "id": str(entry.id)}


@router.get("/check")
async def check_hospital_status(
    insurer_name: str,
    hospital_name: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Look up the most recent crowdsourced report(s) for this insurer +
    hospital (fuzzy match via ILIKE, since names are rarely typed
    identically). Returns an empty list — not an error — if nobody has
    reported on this pair yet; that's expected for a crowdsourced dataset
    early on.
    """
    result = await db.execute(
        select(NetworkHospital)
        .where(
            NetworkHospital.insurer_name.ilike(f"%{insurer_name.strip()}%"),
            NetworkHospital.hospital_name.ilike(f"%{hospital_name.strip()}%"),
        )
        .order_by(NetworkHospital.created_at.desc())
        .limit(10)
    )
    reports = result.scalars().all()

    return {
        "query": {"insurer_name": insurer_name, "hospital_name": hospital_name},
        "reports": [
            {
                "id": str(r.id),
                "insurer_name": r.insurer_name,
                "hospital_name": r.hospital_name,
                "city": r.city,
                "status": r.status,
                "note": r.note,
                "reported_on": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ],
        "most_recent_status": reports[0].status if reports else "unknown",
        "disclaimer": (
            "Crowdsourced from other users, not an official insurer feed — always confirm directly with the "
            "hospital or insurer before assuming cashless coverage, especially before a planned admission."
        ),
    }
