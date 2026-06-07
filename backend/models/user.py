from typing import Optional

from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    subscription_tier: str = "free"
    analyses_this_month: int = 0


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
