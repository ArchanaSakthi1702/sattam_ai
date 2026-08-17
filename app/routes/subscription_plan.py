from fastapi import Depends,Query,APIRouter,HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime
from uuid import UUID
import logging
from app.schemas.subscription_plan_schemas import VerifyPaymentRequest
from app.database import get_db
from app.models import User
from app.services.subscription_plan_service import SubscriptionService
from app.auth.dependencies import get_current_user



logger=logging.getLogger(__name__)


router=APIRouter(
    prefix="/subscription-plans",
    tags=["User Subscription"]
)


@router.get("/list-plans")
async def list_subscription_plans(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    cursor: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await SubscriptionService.list_plans(
        db=db,
        limit=limit,
        cursor=cursor,
    )


@router.get("/me")
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    try:
        subscription = (
            await SubscriptionService
            .get_user_subscription(
                db,
                current_user,
            )
        )

        return {
            "subscription_id": str(
                subscription.id
            ),
            "is_active": (
                subscription.is_active
            ),
            "started_at": (
                subscription.started_at
            ),
            "expires_at": (
                subscription.expires_at
            ),
            "plan": {
                "id": str(
                    subscription.plan.id
                ),
                "name": (
                    subscription.plan.name
                ),
                "description": (
                    subscription.plan.description
                ),
                "daily_ai_limit": (
                    subscription.plan.daily_ai_limit
                ),
                "monthly_ai_limit": (
                    subscription.plan.monthly_ai_limit
                ),
                "max_storage_mb": (
                    subscription.plan.max_storage_mb
                ),
                "max_files": (
                    subscription.plan.max_files
                ),
                "price": (
                    subscription.plan.price
                ),
            },
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except Exception as e:
        logger.exception(
            "Failed to fetch subscription"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Failed to fetch subscription"
            ),
        )

@router.post("/subscribe/{plan_id}")
async def subscribe_to_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await SubscriptionService.subscribe_to_plan(
            db=db,
            user=current_user,
            plan_id=plan_id,
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post("/create-order/{plan_id}")
async def create_order(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await SubscriptionService.create_order(
            db=db,
            user=current_user,
            plan_id=plan_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post("/verify-payment")
async def verify_payment(
    payload: VerifyPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await SubscriptionService.verify_payment(
        db=db,
        user=current_user,
        payload=payload,
    )



@router.get("/ai-usage")
async def get_ai_usage(
    current_user: User = Depends(
        get_current_user
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await SubscriptionService.get_ai_usage(
        db=db,
        user=current_user,
    )


