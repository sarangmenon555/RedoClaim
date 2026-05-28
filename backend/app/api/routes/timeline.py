"""Timeline API route."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.models import Claim
from app.api.deps.auth import get_current_user

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
        if c.gro_deadline:
            days_left = (c.gro_deadline - now).days
            if 0 <= days_left <= 7:
                urgent.append({
                    "claim_id": str(c.id),
                    "insurer_name": c.insurer_name,
                    "deadline_type": "GRO",
                    "deadline_date": c.gro_deadline.isoformat(),
                    "days_left": days_left,
                })
        if c.irdai_deadline:
            days_left = (c.irdai_deadline - now).days
            if 0 <= days_left <= 14:
                urgent.append({
                    "claim_id": str(c.id),
                    "insurer_name": c.insurer_name,
                    "deadline_type": "Ombudsman",
                    "deadline_date": c.irdai_deadline.isoformat(),
                    "days_left": days_left,
                })

    return {
        "total_claims": len(claims),
        "urgent_deadlines": sorted(urgent, key=lambda x: x["days_left"]),
        "irdai_violations": sum(1 for c in claims if c.irdai_violation),
    }
