from datetime import datetime, timezone

from fastapi import HTTPException

from backend.config import settings
from backend.database import supabase


def _month_key() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year}-{now.month:02d}"


async def check_and_increment_usage(user_id: str):
    sub = supabase.table("subscriptions").select("tier").eq("user_id", user_id).execute()
    tier = sub.data[0]["tier"] if sub.data else "free"

    if tier == "pro":
        return

    month = _month_key()
    result = (
        supabase.table("monthly_usage")
        .select("count")
        .eq("user_id", user_id)
        .eq("month", month)
        .execute()
    )
    current = result.data[0]["count"] if result.data else 0

    if current >= settings.FREE_TIER_LIMIT:
        raise HTTPException(
            status_code=402,
            detail=f"Free tier limit of {settings.FREE_TIER_LIMIT} analyses/month reached. Upgrade to Pro.",
        )

    supabase.table("monthly_usage").upsert({
        "user_id": user_id,
        "month": month,
        "count": current + 1,
    }).execute()


async def get_usage(user_id: str) -> dict:
    month = _month_key()
    result = (
        supabase.table("monthly_usage")
        .select("count")
        .eq("user_id", user_id)
        .eq("month", month)
        .execute()
    )
    count = result.data[0]["count"] if result.data else 0
    sub = supabase.table("subscriptions").select("tier").eq("user_id", user_id).execute()
    tier = sub.data[0]["tier"] if sub.data else "free"
    return {
        "tier": tier,
        "used": count,
        "limit": None if tier == "pro" else settings.FREE_TIER_LIMIT,
    }
