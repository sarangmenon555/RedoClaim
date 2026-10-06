"""Timeline API route."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.models import Claim
from app.api.deps.auth import get_current_user
from app.services.irdai.timeline_model import current_deadline

router = APIRouter()


@router.get("/summary")
async def get_timeline_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get dashboard timeline summary with deadline counts."""
    now = datetime.now()
    week_later = now + timedelta(days=7)

    result = await db.execute(
        select(Claim).where(Claim.owner_id == current_user.id)
    )
    claims = result.scalars().all()

    urgent = []
    for c in claims:
        gro_due = current_deadline(c, "gro_deadline")
        if gro_due:
            days_left = (gro_due.replace(tzinfo=None) - now).days
            if 0 <= days_left <= 7:
                urgent.append({
                    "claim_id": str(c.id),
                    "insurer_name": c.insurer_name,
                    "deadline_type": "Insurer grievance response (TAT)",
                    "deadline_kind": "tat",
                    "deadline_date": gro_due.isoformat(),
                    "days_left": days_left,
                })
        window = current_deadline(c, "irdai_deadline")
        if window:
            days_left = (window.replace(tzinfo=None) - now).days
            if 0 <= days_left <= 14:
                urgent.append({
                    "claim_id": str(c.id),
                    "insurer_name": c.insurer_name,
                    "deadline_type": "Indicative Ombudsman window",
                    "deadline_kind": "limitation_indicative",
                    "deadline_date": window.isoformat(),
                    "days_left": days_left,
                })

    return {
        "total_claims": len(claims),
        "urgent_deadlines": sorted(urgent, key=lambda x: x["days_left"]),
        "irdai_violations": sum(1 for c in claims if c.irdai_violation),
    }
