from datetime import datetime, timezone
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    User,
    UserSubscription,
    UserAIUsage,
)


logger = logging.getLogger(__name__)


class SubscriptionGuardService:

    @staticmethod
    async def get_active_subscription(
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

    @staticmethod
    async def get_usage(
        db: AsyncSession,
        user: User,
    ) -> UserAIUsage:

        usage = await db.scalar(
            select(UserAIUsage)
            .where(
                UserAIUsage.user_id == user.id,
            )
            .with_for_update()
        )

        if not usage:
            usage = UserAIUsage(
                user_id=user.id,
            )

            db.add(usage)

            await db.flush()

            usage = await db.scalar(
                select(UserAIUsage)
                .where(
                    UserAIUsage.user_id == user.id,
                )
                .with_for_update()
            )

        return usage

    @staticmethod
    async def reset_usage_if_needed(
        usage: UserAIUsage,
    ) -> None:

        now = datetime.now(timezone.utc)

        if usage.last_daily_reset.date() != now.date():

            usage.daily_tokens_used = 0
            usage.last_daily_reset = now

        if (
            usage.last_monthly_reset.month != now.month
            or
            usage.last_monthly_reset.year != now.year
        ):

            usage.monthly_tokens_used = 0
            usage.last_monthly_reset = now

    @staticmethod
    async def validate_usage_limits(
        subscription: UserSubscription,
        usage: UserAIUsage,
    ) -> None:

        plan = subscription.plan

        if (
            plan.daily_ai_limit is not None
            and usage.daily_tokens_used
            >= plan.daily_ai_limit
        ):
            raise ValueError(
                "Daily token limit exceeded"
            )

        if (
            plan.monthly_ai_limit is not None
            and usage.monthly_tokens_used
            >= plan.monthly_ai_limit
        ):
            raise ValueError(
                "Monthly token limit exceeded"
            )

    @staticmethod
    async def consume_tokens(
        subscription: UserSubscription,
        usage: UserAIUsage,
        total_tokens: int,
    ) -> None:
        """
        Records token usage for a completion that has already been
        generated (and billed by the upstream provider).

        Note: the pre-call check (validate_usage_limits) is what
        gates *starting* a new request. By the time we get here the
        model has already run and the user has already been charged
        for it upstream, so we must not raise and discard the
        response just because this call happened to push the user
        over their limit - that would mean paying for a completion
        and then throwing it away. Instead we record the usage
        (allowing it to go over the cap for this one call) and log
        the overage so it can be monitored/alerted on. The *next*
        request will be blocked by validate_usage_limits as normal.
        """

        plan = subscription.plan

        usage.daily_tokens_used += total_tokens
        usage.monthly_tokens_used += total_tokens

        if (
            plan.daily_ai_limit is not None
            and usage.daily_tokens_used > plan.daily_ai_limit
        ):
            logger.warning(
                "User %s exceeded daily AI token limit "
                "(used=%s, limit=%s) as a result of completing an "
                "in-flight request.",
                subscription.user_id,
                usage.daily_tokens_used,
                plan.daily_ai_limit,
            )

        if (
            plan.monthly_ai_limit is not None
            and usage.monthly_tokens_used > plan.monthly_ai_limit
        ):
            logger.warning(
                "User %s exceeded monthly AI token limit "
                "(used=%s, limit=%s) as a result of completing an "
                "in-flight request.",
                subscription.user_id,
                usage.monthly_tokens_used,
                plan.monthly_ai_limit,
            )