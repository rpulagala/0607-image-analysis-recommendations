from fastapi import APIRouter, Depends

from backend.middleware.auth_guard import get_current_user
from backend.models.subscription import CheckoutSessionRequest
from backend.services.stripe_service import (
    create_billing_portal_session,
    create_checkout_session,
)
from backend.services.usage import get_usage

router = APIRouter()


@router.post("/billing/checkout")
async def checkout(payload: CheckoutSessionRequest, user=Depends(get_current_user)):
    url = await create_checkout_session(
        user_id=user["id"],
        email=user["email"],
        price_id=payload.price_id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
    )
    return {"url": url}


@router.post("/billing/portal")
async def billing_portal(return_url: str, user=Depends(get_current_user)):
    url = await create_billing_portal_session(user["id"], return_url)
    return {"url": url}


@router.get("/billing/usage")
async def usage(user=Depends(get_current_user)):
    return await get_usage(user["id"])
