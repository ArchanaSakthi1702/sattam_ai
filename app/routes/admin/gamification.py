from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.auth.dependencies import get_current_staff
from app.models import User

from app.schemas.game_level_schemas import CreateLevelRequest
from app.schemas.game_question_schemas import CreateQuestionRequest
from app.services.game_level_service import GameLevelService
from app.services.game_question_service import GameQuestionService


router = APIRouter(
    prefix="/admin/gamification",
    tags=["Admin Gamification"],
)


@router.post("/create-level")
async def create_level(
    payload: CreateLevelRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: User = Depends(get_current_staff),
):
    try:
        return await GameLevelService.create_level(
            db=db,
            level_number=payload.level_number,
            title=payload.title,
            topic=payload.topic,
            difficulty=payload.difficulty,
            min_exp_to_enter=payload.min_exp_to_enter,
            prerequisite_level_id=payload.prerequisite_level_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    


@router.post("/create-question/{level_id}")
async def create_question(
    level_id: UUID,
    payload: CreateQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: User = Depends(get_current_staff),
):
    try:
        return await GameQuestionService.create_question(
            db=db,
            level_id=level_id,
            order_index=payload.order_index,
            question_text=payload.question_text,
            question_type=payload.question_type,
            options=payload.options,
            correct_answer=payload.correct_answer,
            explanation=payload.explanation,
            exp_reward=payload.exp_reward,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    

