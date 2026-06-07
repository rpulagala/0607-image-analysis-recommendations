import uuid

from fastapi import HTTPException, UploadFile

from backend.database import supabase

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
BUCKET = "user-images"


async def upload_image(file: UploadFile, user_id: str) -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WEBP images are allowed")

    contents = await file.read()
    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Image must be under 10 MB")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    path = f"{user_id}/{uuid.uuid4()}.{ext}"

    supabase.storage.from_(BUCKET).upload(
        path=path,
        file=contents,
        file_options={"content-type": file.content_type},
    )

    return supabase.storage.from_(BUCKET).get_public_url(path)
