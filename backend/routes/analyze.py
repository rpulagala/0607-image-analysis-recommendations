import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, UploadFile

from backend.database import supabase
from backend.middleware.auth_guard import get_current_user
from backend.models.analysis import AnalysisResponse
from backend.services.ai_analysis import analyze_image
from backend.services.recommendations import generate_recommendations
from backend.services.storage import upload_image
from backend.services.usage import check_and_increment_usage

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    await check_and_increment_usage(user["id"])

    image_url = await upload_image(file, user["id"])
    analysis = await analyze_image(image_url)
    recommendations = await generate_recommendations(analysis)

    record_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    supabase.table("analyses").insert({
        "id": record_id,
        "user_id": user["id"],
        "image_url": image_url,
        "analysis": analysis.model_dump(),
        "recommendations": [r.model_dump() for r in recommendations],
        "created_at": now,
    }).execute()

    return AnalysisResponse(
        id=record_id,
        image_url=image_url,
        analysis=analysis,
        recommendations=recommendations,
        created_at=now,
    )
