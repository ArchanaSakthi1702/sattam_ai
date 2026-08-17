from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.helpers.time_control import utc_now
from datetime import timedelta,datetime

from app.models import (
    User,
    UserGamification,
    AccountLevel,
    UserLevelProgress,
    UserBadge,
    GameLevel,
    PointsLedgerEntry
)



class GamificationService:

    @staticmethod
    async def get_profile(
        db: AsyncSession,
        user: User,
    ) -> dict:

        gamification = await db.get(
            UserGamification,
            user.id,
        )

        if not gamification:
            raise ValueError(
                "Gamification profile not found"
            )
        
        await GamificationService.refresh_hearts(
            db=db,
            user_id=user.id
        )


        account_level = await db.scalar(
            select(AccountLevel)
            .where(
                AccountLevel.exp_required
                <= gamification.total_exp
            )
            .order_by(
                AccountLevel.exp_required.desc()
            )
            .limit(1)
        )

        next_level = await db.scalar(
            select(AccountLevel)
            .where(
                AccountLevel.exp_required
                > gamification.total_exp
            )
            .order_by(
                AccountLevel.exp_required.asc()
            )
            .limit(1)
        )

        completed_levels = await db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        UserLevelProgress.times_completed
                    ),
                    0,
                )
            )
            .where(
                UserLevelProgress.user_id == user.id
            )
        )

        badges_count = await db.scalar(
            select(func.count(UserBadge.id))
            .where(
                UserBadge.user_id == user.id
            )
        )

        return {
            "total_exp": gamification.total_exp,
            "account_level": (
                account_level.level_number
                if account_level
                else 1
            ),
            "account_title": (
                account_level.title
                if account_level
                else "Beginner"
            ),
            "current_level_exp_required": (
                account_level.exp_required
                if account_level
                else 0
            ),
            "next_level_exp_required": (
                next_level.exp_required
                if next_level
                else None
            ),
            "exp_to_next_level": (
                next_level.exp_required
                - gamification.total_exp
                if next_level
                else 0
            ),
            "hearts_current": gamification.hearts_current,
            "hearts_max": gamification.hearts_max,
            "winning_streak": gamification.winning_streak,
            "longest_winning_streak":
                gamification.longest_winning_streak,
            "login_streak": gamification.login_streak,
            "longest_login_streak":
                gamification.longest_login_streak,
            "levels_completed": completed_levels,
            "badges_count": badges_count,
            "leaderboard_opt_in":
                gamification.leaderboard_opt_in,
        }
    

    
    @staticmethod
    async def refresh_hearts(
        db: AsyncSession,
        user_id: UUID,
    ) -> None:

        gamification = await db.get(
            UserGamification,
            user_id,
        )

        if not gamification:
            raise ValueError(
                "Gamification profile not found"
            )

        if (
            gamification.hearts_current
            >= gamification.hearts_max
        ):
            return

        now = utc_now()

        elapsed_seconds = (
            now - gamification.last_heart_regen_at
        ).total_seconds()

        hearts_to_add = int(
            elapsed_seconds // 300
        )

        if hearts_to_add <= 0:
            return

        new_hearts = min(
            gamification.hearts_max,
            gamification.hearts_current + hearts_to_add,
        )

        actual_added = (
            new_hearts - gamification.hearts_current
        )

        gamification.hearts_current = new_hearts

        gamification.last_heart_regen_at += timedelta(
            seconds=actual_added * 300
        )

        await db.commit()


    
    @staticmethod
    async def get_user_badges(
        db: AsyncSession,
        user: User,
    ) -> list[dict]:

        badges = await db.scalars(
            select(UserBadge)
            .options(
                selectinload(UserBadge.badge)
            )
            .where(
                UserBadge.user_id == user.id
            )
            .order_by(
                UserBadge.earned_at.desc()
            )
        )

        return [
            {
                "badge_id": item.badge.id,
                "code": item.badge.code,
                "name": item.badge.name,
                "description": item.badge.description,
                "icon_url": item.badge.icon_url,
                "earned_at": item.earned_at,
            }
            for item in badges
        ]
    

    
    @staticmethod
    async def get_level_progress(
        db: AsyncSession,
        user: User,
        limit: int = 20,
        cursor: datetime | None = None,
    ) -> dict:

        query = (
            select(UserLevelProgress)
            .options(
                selectinload(
                    UserLevelProgress.level
                )
            )
            .where(
                UserLevelProgress.user_id == user.id
            )
            .order_by(
                UserLevelProgress.created_at.desc()
            )
        )

        if cursor:
            query = query.where(
                UserLevelProgress.created_at < cursor
            )

        query = query.limit(limit + 1)

        result = await db.scalars(query)

        progress = list(result)

        has_more = len(progress) > limit

        if has_more:
            progress = progress[:limit]

        next_cursor = (
            progress[-1].created_at
            if has_more and progress
            else None
        )

        return {
            "items": [
                {
                    "level_id": item.level.id,
                    "level_number": item.level.level_number,
                    "title": item.level.title,
                    "topic": item.level.topic,
                    "difficulty": item.level.difficulty,

                    "times_played": item.times_played,
                    "times_completed": item.times_completed,
                    "times_perfect": item.times_perfect,

                    "first_completed_at": item.first_completed_at,
                    "last_played_at": item.last_played_at,
                    "created_at": item.created_at,
                }
                for item in progress
            ],
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    
    @staticmethod
    async def get_points_ledger(
        db: AsyncSession,
        user: User,
        limit: int = 20,
        cursor: datetime | None = None,
    ) -> dict:

        query = (
            select(PointsLedgerEntry)
            .where(
                PointsLedgerEntry.user_id == user.id
            )
            .order_by(
                PointsLedgerEntry.created_at.desc()
            )
        )

        if cursor:
            query = query.where(
                PointsLedgerEntry.created_at < cursor
            )

        query = query.limit(limit + 1)

        result = await db.scalars(query)

        entries = list(result)

        has_more = len(entries) > limit

        if has_more:
            entries = entries[:limit]

        next_cursor = (
            entries[-1].created_at
            if has_more and entries
            else None
        )

        return {
            "items": [
                {
                    "id": item.id,
                    "points": item.points,
                    "reason": item.reason,
                    "meta": item.meta,
                    "created_at": item.created_at,
                }
                for item in entries
            ],
            "next_cursor": next_cursor,
            "has_more": has_more,
        }