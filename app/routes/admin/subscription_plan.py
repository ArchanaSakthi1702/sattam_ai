from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_staff

from app.schemas.subscription_plan_schemas import (
    CreateSubscriptionPlanRequest,
    AssignPlanRequest
)

from app.services.subscription_plan_service import (
    SubscriptionService
)

router = APIRouter(
    prefix="/admin/subscriptions",
    tags=["Admin Subscriptions"],
    dependencies=[Depends(get_current_staff)]
)


@router.post(
    "/create-plan",
    status_code=status.HTTP_201_CREATED,
)
async def create_plan(
    payload: CreateSubscriptionPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        plan = await SubscriptionService.create_plan(
            db=db,
            data=payload,
        )

        return {
            "message": "Subscription plan created successfully",
            "plan": {
                "id": str(plan.id),
                "name": plan.name,
                "price": plan.price,
                "daily_ai_limit": plan.daily_ai_limit,
                "monthly_ai_limit": plan.monthly_ai_limit,
                "max_storage_mb": plan.max_storage_mb,
                "max_files": plan.max_files,
            },
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    

@router.post(
    "/assign-plan-to-user",
    status_code=status.HTTP_201_CREATED,
)
async def assign_subscription(
    payload: AssignPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        subscription = await SubscriptionService.assign_plan(
            db=db,
            data=payload,
        )

        return {
            "message": "Subscription assigned successfully",
            "subscription_id": str(subscription.id),
            "user_id": str(subscription.user_id),
            "plan_id": str(subscription.plan_id),
            "is_active": subscription.is_active,
            "expires_at": subscription.expires_at,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )