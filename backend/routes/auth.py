from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr

from backend.database import supabase

router = APIRouter()


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
async def signup(payload: SignUpRequest):
    try:
        response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
            "options": {"data": {"full_name": payload.full_name}},
        })
        if response.user is None:
            raise HTTPException(status_code=400, detail="Signup failed")
        return {"user_id": response.user.id, "message": "Verification email sent"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/signin")
async def signin(payload: SignInRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user_id": response.user.id,
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/signout")
async def signout(authorization: str = Header(...)):
    supabase.auth.sign_out()
    return {"message": "Signed out"}
