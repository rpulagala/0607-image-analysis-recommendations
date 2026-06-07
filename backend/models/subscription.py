from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SubscriptionTier(str, Enum):
    free = "free"
    pro = "pro"


class SubscriptionStatus(str, Enum):
    active = "active"
    canceled = "canceled"
    past_due = "past_due"


class Subscription(BaseModel):
    id: str
    user_id: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    tier: SubscriptionTier = SubscriptionTier.free
    status: SubscriptionStatus = SubscriptionStatus.active
    current_period_end: Optional[datetime] = None


class CheckoutSessionRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str
