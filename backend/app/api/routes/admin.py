"""Admin API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.models import User, Document, Claim, Appeal
from app.api.deps.auth import get_admin_user

router = APIRouter()


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_admin_user),
):
    """Platform-wide statistics for admin dashboard."""
    user_count = await db.scalar(select(func.count(User.id)))
    doc_count = await db.scalar(select(func.count(Document.id)))
    claim_count = await db.scalar(select(func.count(Claim.id)))
    appeal_count = await db.scalar(select(func.count(Appeal.id)))
    violation_count = await db.scalar(
        select(func.count(Claim.id)).where(Claim.irdai_violation == True)
    )

    return {
        "users": user_count,
        "documents": doc_count,
        "claims": claim_count,
        "appeals": appeal_count,
        "irdai_violations_found": violation_count,
    }
