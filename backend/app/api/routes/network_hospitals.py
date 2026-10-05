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
from datetime import datetime

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


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


_STALE_AFTER_DAYS = 180

UNVERIFIED_WARNING = (
    "Community report — not verified. This information may be outdated. "
    "Confirm directly with the insurer/hospital before admission."
)


@router.get("/check")
async def check_hospital_status(
    insurer_name: str,
    hospital_name: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Look up crowdsourced reports for this insurer + hospital.

    Only reports whose insurer AND hospital names match the query exactly
    (case-insensitive) drive `most_recent_status`. Looser partial matches are
    returned separately as `possible_matches` with their own names, so a
    report about a different hospital/branch/insurer is never presented as
    the answer. Nothing here is an official insurer feed.
    """
    ins = insurer_name.strip()
    hos = hospital_name.strip()
    result = await db.execute(
        select(NetworkHospital)
        .where(
            NetworkHospital.insurer_name.ilike(f"%{_escape_like(ins)}%", escape="\\"),
            NetworkHospital.hospital_name.ilike(f"%{_escape_like(hos)}%", escape="\\"),
        )
        .order_by(NetworkHospital.created_at.desc())
        .limit(30)
    )
    matches = result.scalars().all()

    def _is_exact(r) -> bool:
        return (r.insurer_name or "").strip().lower() == ins.lower() and \
               (r.hospital_name or "").strip().lower() == hos.lower()

    exact = [r for r in matches if _is_exact(r)][:10]
    possible = [r for r in matches if not _is_exact(r)][:5]

    def _ser(r):
        return {
            "id": str(r.id),
            "insurer_name": r.insurer_name,
            "hospital_name": r.hospital_name,
            "city": r.city,
            "status": r.status,
            "note": r.note,
            "reported_on": r.created_at.isoformat() if r.created_at else None,
        }

    latest = exact[0].created_at if exact else None
    possibly_outdated = True
    if latest is not None:
        now = datetime.now(latest.tzinfo) if latest.tzinfo else datetime.utcnow()
        possibly_outdated = (now - latest).days > _STALE_AFTER_DAYS

    return {
        "query": {"insurer_name": insurer_name, "hospital_name": hospital_name},
        "reports": [_ser(r) for r in exact],
        "possible_matches": [_ser(r) for r in possible],
        "most_recent_status": exact[0].status if exact else "unknown",
        "most_recent_reported_on": latest.isoformat() if latest else None,
        "possibly_outdated": possibly_outdated,
        "source": "community_report",
        "verification_status": "unverified",
        "warning": UNVERIFIED_WARNING,
        "disclaimer": (
            "Crowdsourced from other users, not an official insurer feed, and not verified. Network lists "
            "change often. Always confirm directly with the hospital or insurer before assuming cashless "
            "coverage, especially before a planned admission."
        ),
    }
