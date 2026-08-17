# app/schemas/subscription/create_plan.py

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class CreateSubscriptionPlanRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None

    daily_ai_limit: int = 10000
    monthly_ai_limit: int = 300000

    max_storage_mb: int = 100
    max_files: int = 10

    price: int = 0



class AssignPlanRequest(BaseModel):
    user_id: UUID
    plan_id: UUID
    expires_at: datetime | None = None



class SubscriptionPlanResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    daily_ai_limit: int
    monthly_ai_limit: int
    max_storage_mb: int
    max_files: int
    price: int



class SubscriptionPlanListResponse(BaseModel):
    items: list[SubscriptionPlanResponse]
    next_cursor: UUID | None
    has_more: bool
    

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str