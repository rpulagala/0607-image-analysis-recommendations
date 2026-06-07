from fastapi import APIRouter, Depends

from backend.database import supabase
from backend.middleware.auth_guard import get_current_user
from backend.models.user import UpdateProfileRequest

router = APIRouter()


@router.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    profile = (
        supabase.table("profiles").select("*").eq("id", user["id"]).single().execute()
    )
    usage = (
        supabase.table("monthly_usage")
        .select("count")
        .eq("user_id", user["id"])
        .execute()
    )
    count = usage.data[0]["count"] if usage.data else 0
    return {**profile.data, "analyses_this_month": count}


@router.patch("/profile")
async def update_profile(
    payload: UpdateProfileRequest, user=Depends(get_current_user)
):
    supabase.table("profiles").update(
        payload.model_dump(exclude_none=True)
    ).eq("id", user["id"]).execute()
    return {"message": "Profile updated"}
