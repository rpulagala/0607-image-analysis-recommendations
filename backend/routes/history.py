from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.database import supabase
from backend.middleware.auth_guard import get_current_user

router = APIRouter()


@router.get("/history")
async def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    search: Optional[str] = None,
    user=Depends(get_current_user),
):
    offset = (page - 1) * limit
    query = (
        supabase.table("analyses")
        .select("id, image_url, analysis->>description, created_at")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    response = query.execute()
    return {"items": response.data, "page": page, "limit": limit}


@router.get("/history/{analysis_id}")
async def get_analysis(analysis_id: str, user=Depends(get_current_user)):
    response = (
        supabase.table("analyses")
        .select("*")
        .eq("id", analysis_id)
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )
    if response.data is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return response.data
