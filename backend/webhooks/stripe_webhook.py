import stripe
from fastapi import APIRouter, Header, HTTPException, Request

from backend.config import settings
from backend.database import supabase

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature"),
):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        _handle_checkout_completed(event["data"]["object"])
    elif event["type"] in ("customer.subscription.updated", "customer.subscription.deleted"):
        _handle_subscription_change(event["data"]["object"])

    return {"received": True}


def _handle_checkout_completed(session: dict):
    user_id = session["metadata"]["user_id"]
    supabase.table("subscriptions").update({
        "tier": "pro",
        "stripe_subscription_id": session.get("subscription"),
        "status": "active",
    }).eq("user_id", user_id).execute()


def _handle_subscription_change(subscription: dict):
    status = subscription["status"]
    supabase.table("subscriptions").update({
        "tier": "pro" if status == "active" else "free",
        "status": status,
        "current_period_end": subscription.get("current_period_end"),
    }).eq("stripe_customer_id", subscription["customer"]).execute()
