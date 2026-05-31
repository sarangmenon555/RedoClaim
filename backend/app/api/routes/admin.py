"""Admin API routes — expanded stats for internal dashboard."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.models.models import User, Document, Claim, Appeal, UserRole, ClaimStatus
from app.api.deps.auth import get_admin_user

router = APIRouter()


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_admin_user),
):
    """Platform-wide statistics for admin dashboard."""
    now = datetime.now(timezone.utc)
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)

    # ── Totals ─────────────────────────────────────────────────────────────
    user_count = await db.scalar(select(func.count(User.id)))
    doc_count = await db.scalar(select(func.count(Document.id)))
    claim_count = await db.scalar(select(func.count(Claim.id)))
    appeal_count = await db.scalar(select(func.count(Appeal.id)))
    violation_count = await db.scalar(
        select(func.count(Claim.id)).where(Claim.irdai_violation == True)
    )

    # ── New users (last 7 & 30 days) ───────────────────────────────────────
    new_users_7d = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= last_7_days)
    )
    new_users_30d = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= last_30_days)
    )

    # ── Active vs inactive users ────────────────────────────────────────────
    active_users = await db.scalar(
        select(func.count(User.id)).where(User.is_active == True)
    )
    verified_users = await db.scalar(
        select(func.count(User.id)).where(User.is_verified == True)
    )

    # ── Claim status breakdown ──────────────────────────────────────────────
    claim_status_rows = await db.execute(
        select(Claim.status, func.count(Claim.id))
        .group_by(Claim.status)
    )
    claim_by_status = {str(row[0]): row[1] for row in claim_status_rows.all()}

    # ── Daily user signups for the last 30 days ─────────────────────────────
    daily_signups_rows = await db.execute(
        select(
            cast(User.created_at, Date).label("day"),
            func.count(User.id).label("count"),
        )
        .where(User.created_at >= last_30_days)
        .group_by(cast(User.created_at, Date))
        .order_by(cast(User.created_at, Date))
    )
    daily_signups = [
        {"date": str(row.day), "count": row.count}
        for row in daily_signups_rows.all()
    ]

    # ── Recent 10 registered users ──────────────────────────────────────────
    recent_users_rows = await db.execute(
        select(User.id, User.full_name, User.email, User.created_at, User.is_active, User.is_verified)
        .order_by(User.created_at.desc())
        .limit(10)
    )
    recent_users = [
        {
            "id": str(row.id),
            "full_name": row.full_name,
            "email": row.email,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "is_active": row.is_active,
            "is_verified": row.is_verified,
        }
        for row in recent_users_rows.all()
    ]

    return {
        # Totals
        "users": user_count,
        "documents": doc_count,
        "claims": claim_count,
        "appeals": appeal_count,
        "irdai_violations_found": violation_count,
        # User breakdown
        "new_users_7d": new_users_7d,
        "new_users_30d": new_users_30d,
        "active_users": active_users,
        "verified_users": verified_users,
        # Claim breakdown
        "claim_by_status": claim_by_status,
        # Time series
        "daily_signups": daily_signups,
        # Recent activity
        "recent_users": recent_users,
    }