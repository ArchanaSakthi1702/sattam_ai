# app/services/subscription_service.py
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import time

from uuid import UUID

from datetime import datetime,timedelta

from app.models import (
    User,
    SubscriptionPlan,
    UserSubscription,
    UserAIUsage,
    Payment,
)

from app.schemas.subscription_plan_schemas import (
    CreateSubscriptionPlanRequest,
    AssignPlanRequest,
    VerifyPaymentRequest
)
from app.helpers.razor_pay_client import client
from app.helpers.time_control import utc_now
from app.config import get_settings

settings=get_settings()


class SubscriptionService:
    """
    Service for managing subscription plans
    and user subscriptions.
    """

    @staticmethod
    async def create_plan(
        db: AsyncSession,
        data: CreateSubscriptionPlanRequest,
    ) -> SubscriptionPlan:

        existing_plan = await db.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.name == data.name,
            )
        )

        if existing_plan:
            raise ValueError(
                "Subscription plan already exists"
            )

        plan = SubscriptionPlan(
            name=data.name,
            description=data.description,
            daily_ai_limit=data.daily_ai_limit,
            monthly_ai_limit=data.monthly_ai_limit,
            max_storage_mb=data.max_storage_mb,
            max_files=data.max_files,
            price=data.price,
        )

        db.add(plan)

        await db.commit()
        await db.refresh(plan)

        return plan
    

    @staticmethod
    async def assign_plan(
        db: AsyncSession,
        data: AssignPlanRequest,
    ) -> UserSubscription:

        user = await db.scalar(
            select(User).where(
                User.id == data.user_id,
                User.is_deleted.is_(False),
            )
        )

        if not user:
            raise ValueError("User not found")

        plan = await db.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.id == data.plan_id,
            )
        )

        if not plan:
            raise ValueError(
                "Subscription plan not found"
            )

        await db.execute(
            update(UserSubscription)
            .where(
                UserSubscription.user_id == data.user_id,
                UserSubscription.is_active.is_(True),
            )
            .values(
                is_active=False,
            )
        )

        subscription = UserSubscription(
            user_id=data.user_id,
            plan_id=data.plan_id,
            expires_at=data.expires_at,
            is_active=True,
        )

        db.add(subscription)

        await db.commit()
        await db.refresh(subscription)

        return subscription
    


    @staticmethod
    async def list_plans(
        db: AsyncSession,
        limit: int = 20,
        cursor: datetime | None = None,
    ) -> dict:

        query = (
            select(SubscriptionPlan)
            .order_by(
                SubscriptionPlan.created_at.desc()
            )
        )

        if cursor:
            query = query.where(
                SubscriptionPlan.created_at < cursor
            )

        query = query.limit(limit + 1)

        result = await db.scalars(query)

        plans = list(result)

        has_more = len(plans) > limit

        if has_more:
            plans = plans[:limit]

        next_cursor = (
            plans[-1].created_at
            if has_more and plans
            else None
        )

        return {
            "items": plans,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    

    @staticmethod
    async def get_user_subscription(
        db: AsyncSession,
        user: User,
    ) -> UserSubscription:

        subscription = await db.scalar(
            select(UserSubscription)
            .options(
                selectinload(UserSubscription.plan)
            )
            .where(
                UserSubscription.user_id == user.id,
                UserSubscription.is_active.is_(True),
            )
        )

        if not subscription:
            raise ValueError(
                "No active subscription found"
            )

        return subscription
    

    staticmethod
    async def subscribe_to_plan(
        db: AsyncSession,
        user: User,
        plan_id,
    ) -> UserSubscription:

        plan = await db.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.id == plan_id
            )
        )

        if not plan:
            raise ValueError(
                "Subscription plan not found"
            )

        if plan.price > 0:
            raise PermissionError(
                "Paid plans require admin approval"
            )

        current_subscription = await db.scalar(
            select(UserSubscription).where(
                UserSubscription.user_id == user.id,
                UserSubscription.is_active.is_(True),
            )
        )

        if (
            current_subscription
            and current_subscription.plan_id == plan.id
        ):
            raise ValueError(
                "Already subscribed to this plan"
            )

        await db.execute(
            update(UserSubscription)
            .where(
                UserSubscription.user_id == user.id,
                UserSubscription.is_active.is_(True),
            )
            .values(
                is_active=False,
            )
        )

        subscription = UserSubscription(
            user_id=user.id,
            plan_id=plan.id,
            is_active=True,
        )

        db.add(subscription)

        await db.commit()
        await db.refresh(subscription)

        return subscription


    @staticmethod
    async def create_order(
        db: AsyncSession,
        user: User,
        plan_id: UUID,
    ):
        active_subscription = await db.scalar(
            select(UserSubscription).where(
                UserSubscription.user_id == user.id,
                UserSubscription.is_active.is_(True),
            )
        )

        if active_subscription:
            raise ValueError(
                "You already have an active subscription plan."
            )

        plan = await db.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.id == plan_id
            )
        )

        if not plan:
            raise ValueError(
                "Subscription plan not found."
            )

        amount_paise = int(plan.price * 100)

        try:
            order = client.order.create(
                {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": f"sub_{user.id.hex[:6]}_{int(time.time())}",
                    "notes": {
                        "user_id": str(user.id),
                        "plan_id": str(plan.id),
                        "plan_name": plan.name,
                    },
                }
            )

            payment = Payment(
                user_id=user.id,
                plan_id=plan.id,
                razorpay_order_id=order["id"],
                amount=plan.price,
                currency="INR",
                status="created",
            )

            db.add(payment)
            await db.commit()

        except Exception as e:
            await db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Failed to create Razorpay order: {str(e)}",
            )

        return {
            "key": settings.RAZORPAY_KEY_ID,
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "plan_name": plan.name,
            "description": plan.description,
        }


    
    @staticmethod
    async def verify_payment(
        db: AsyncSession,
        user: User,
        payload: VerifyPaymentRequest,
    ):
        payment = await db.scalar(
            select(Payment).where(
                Payment.razorpay_order_id
                == payload.razorpay_order_id
            )
        )

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment record not found",
            )

        if payment.user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized payment access",
            )

        if payment.status == "paid":
            raise HTTPException(
                status_code=400,
                detail="Payment already verified",
            )

        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": payload.razorpay_order_id,
                    "razorpay_payment_id": payload.razorpay_payment_id,
                    "razorpay_signature": payload.razorpay_signature,
                }
            )

        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Payment verification failed",
            )

        plan = await db.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.id == payment.plan_id
            )
        )

        if not plan:
            raise HTTPException(
                status_code=404,
                detail="Subscription plan not found",
            )

        active_subscription = await db.scalar(
            select(UserSubscription).where(
                UserSubscription.user_id == user.id,
                UserSubscription.is_active.is_(True),
            )
        )

        if active_subscription:
            raise HTTPException(
                status_code=400,
                detail="User already has an active subscription",
            )

        payment.status = "paid"
        payment.razorpay_payment_id = (
            payload.razorpay_payment_id
        )
        payment.razorpay_signature = (
            payload.razorpay_signature
        )
        payment.paid_at = utc_now()

        subscription = UserSubscription(
            user_id=user.id,
            plan_id=plan.id,
            started_at=utc_now(),
            expires_at=utc_now() + timedelta(days=30),
            is_active=True,
        )

        db.add(subscription)

        await db.commit()

        return {
            "message": "Subscription activated successfully",
            "subscription_id": str(subscription.id),
            "plan_name": plan.name,
            "expires_at": subscription.expires_at,
        }


        



    @staticmethod
    async def get_ai_usage(
        db: AsyncSession,
        user: User,
    ) -> dict:

        usage = await db.get(
            UserAIUsage,
            user.id,
        )

        if not usage:
            raise ValueError(
                "AI usage profile not found"
            )

        subscription = await db.scalar(
            select(UserSubscription)
            .options(
                selectinload(
                    UserSubscription.plan
                )
            )
            .where(
                UserSubscription.user_id == user.id,
                UserSubscription.is_active.is_(True),
            )
        )

        if not subscription:
            raise ValueError(
                "Active subscription not found"
            )

        plan = subscription.plan

        daily_remaining = max(
            0,
            plan.daily_ai_limit
            - usage.daily_tokens_used,
        )

        monthly_remaining = max(
            0,
            plan.monthly_ai_limit
            - usage.monthly_tokens_used,
        )

        return {
            "daily_tokens_used":
                usage.daily_tokens_used,

            "daily_limit":
                plan.daily_ai_limit,

            "daily_remaining":
                daily_remaining,

            "daily_usage_percent":
                round(
                    (
                        usage.daily_tokens_used
                        / plan.daily_ai_limit
                    ) * 100,
                    2,
                )
                if plan.daily_ai_limit
                else 0,

            "monthly_tokens_used":
                usage.monthly_tokens_used,

            "monthly_limit":
                plan.monthly_ai_limit,

            "monthly_remaining":
                monthly_remaining,

            "monthly_usage_percent":
                round(
                    (
                        usage.monthly_tokens_used
                        / plan.monthly_ai_limit
                    ) * 100,
                    2,
                )
                if plan.monthly_ai_limit
                else 0,

            "last_daily_reset":
                usage.last_daily_reset,

            "last_monthly_reset":
                usage.last_monthly_reset,

            "plan_name":
                plan.name,
        }