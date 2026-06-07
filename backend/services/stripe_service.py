import stripe

from backend.config import settings
from backend.database import supabase

stripe.api_key = settings.STRIPE_SECRET_KEY


async def get_or_create_customer(user_id: str, email: str) -> str:
    result = (
        supabase.table("subscriptions")
        .select("stripe_customer_id")
        .eq("user_id", user_id)
        .execute()
    )
    if result.data and result.data[0].get("stripe_customer_id"):
        return result.data[0]["stripe_customer_id"]

    customer = stripe.Customer.create(email=email, metadata={"user_id": user_id})
    supabase.table("subscriptions").upsert({
        "user_id": user_id,
        "stripe_customer_id": customer.id,
        "tier": "free",
    }).execute()
    return customer.id


async def create_checkout_session(
    user_id: str, email: str, price_id: str, success_url: str, cancel_url: str
) -> str:
    customer_id = await get_or_create_customer(user_id, email)
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user_id},
    )
    return session.url


async def create_billing_portal_session(user_id: str, return_url: str) -> str:
    result = (
        supabase.table("subscriptions")
        .select("stripe_customer_id")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    session = stripe.billing_portal.Session.create(
        customer=result.data["stripe_customer_id"],
        return_url=return_url,
    )
    return session.url
