# app/services/game_level_service.py

from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.helpers.time_control import utc_now
from app.models import (GameLevel,User,UserGamification,UserLevelProgress,LevelAttempt)


class GameLevelService:

    @staticmethod
    async def create_level(
        db: AsyncSession,
        level_number: int,
        title: str,
        topic: str | None,
        difficulty: str,
        min_exp_to_enter: int,
        prerequisite_level_id: UUID | None = None,
    ):
        existing_level = await db.scalar(
            select(GameLevel).where(
                GameLevel.level_number == level_number
            )
        )

        if existing_level:
            raise ValueError(
                f"Level {level_number} already exists."
            )

        if prerequisite_level_id:
            prerequisite = await db.get(
                GameLevel,
                prerequisite_level_id,
            )

            if not prerequisite:
                raise ValueError(
                    "Prerequisite level not found."
                )

        level = GameLevel(
            level_number=level_number,
            title=title,
            topic=topic,
            difficulty=difficulty,
            min_exp_to_enter=min_exp_to_enter,
            prerequisite_level_id=prerequisite_level_id,
        )

        db.add(level)

        await db.commit()
        await db.refresh(level)

        return {
            "id": level.id,
            "level_number": level.level_number,
            "title": level.title,
            "topic": level.topic,
            "difficulty": level.difficulty,
            "min_exp_to_enter": level.min_exp_to_enter,
            "prerequisite_level_id": level.prerequisite_level_id,
            "created_at": level.created_at,
        }
    

    @staticmethod
    async def list_levels(
        db: AsyncSession,
        limit: int = 20,
        cursor: datetime | None = None,
    ) -> dict:

        query = (
            select(GameLevel)
            .order_by(
                GameLevel.created_at.desc()
            )
        )

        if cursor:
            query = query.where(
                GameLevel.created_at < cursor
            )

        query = query.limit(limit + 1)

        result = await db.scalars(query)

        levels = list(result)

        has_more = len(levels) > limit

        if has_more:
            levels = levels[:limit]

        next_cursor = (
            levels[-1].created_at
            if has_more and levels
            else None
        )

        return {
            "items": levels,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    

    @staticmethod
    async def get_level(
        db: AsyncSession,
        level_id: UUID,
    ) -> dict:

        level = await db.scalar(
            select(GameLevel)
            .options(
                selectinload(GameLevel.questions)
            )
            .where(
                GameLevel.id == level_id
            )
        )

        if not level:
            raise ValueError("Level not found")

        return {
            "level": level,
            "question_count": len(level.questions),
        }
    

    from sqlalchemy import select

    @staticmethod
    async def start_level(
        db: AsyncSession,
        user: User,
        level_id: UUID,
    ) -> dict:

        level = await db.scalar(
            select(GameLevel)
            .where(
                GameLevel.id == level_id,
                GameLevel.is_active.is_(True),
            )
        )

        if not level:
            raise ValueError("Level not found")

        gamification = await db.scalar(
            select(UserGamification)
            .where(
                UserGamification.user_id == user.id
            )
        )

        if not gamification:
            raise ValueError(
                "Gamification profile not found"
            )

        if gamification.hearts_current <= 0:
            raise ValueError(
                "No hearts remaining"
            )

        if gamification.total_exp < level.min_exp_to_enter:
            raise ValueError(
                "Insufficient EXP for this level"
            )

        if level.prerequisite_level_id:

            prerequisite_completed = await db.scalar(
                select(UserLevelProgress)
                .where(
                    UserLevelProgress.user_id == user.id,
                    UserLevelProgress.level_id
                    == level.prerequisite_level_id,
                    UserLevelProgress.times_completed > 0,
                )
            )

            if not prerequisite_completed:
                raise ValueError(
                    "Prerequisite level not completed"
                )

        attempt = LevelAttempt(
            user_id=user.id,
            level_id=level.id,
        )

        db.add(attempt)

        progress = await db.scalar(
            select(UserLevelProgress)
            .where(
                UserLevelProgress.user_id == user.id,
                UserLevelProgress.level_id == level.id,
            )
        )

        if not progress:
            progress = UserLevelProgress(
                user_id=user.id,
                level_id=level.id,
                times_played=1,
            )
            db.add(progress)

        else:
            progress.times_played += 1
            progress.last_played_at = utc_now()

        await db.commit()
        await db.refresh(attempt)

        return {
            "level_attempt_id": attempt.id,
            "level_id": level.id,
            "level_number": level.level_number,
            "title": level.title,
            "hearts_remaining": gamification.hearts_current,
        }