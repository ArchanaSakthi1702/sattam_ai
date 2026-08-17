from fastapi import APIRouter,Query,Depends,HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from uuid import UUID

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.schemas.game_question_schemas import AnswerQuestionRequest
from app.services.game_level_service import GameLevelService
from app.services.game_question_service import GameQuestionService
from app.services.gamification_service import GamificationService

from app.models import User

router=APIRouter(prefix="/gamification")


@router.get("/list-levels")
async def list_levels(
    limit: int = Query(20, ge=1, le=100),
    cursor: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GameLevelService.list_levels(
        db=db,
        limit=limit,
        cursor=cursor,
    )


@router.get("/get-level-details/{level_id}")
async def get_level(
    level_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GameLevelService.get_level(
        db=db,
        level_id=level_id,
    )

@router.post("/start-level/{level_id}")
async def start_level(
    level_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await GameLevelService.start_level(
            db=db,
            user=current_user,
            level_id=level_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    

@router.post("/answer-question/{question_id}")
async def answer_question(
    question_id: UUID,
    payload: AnswerQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GameQuestionService.answer_question(
        db=db,
        user=current_user,
        question_id=question_id,
        level_attempt_id=payload.level_attempt_id,
        answer=payload.answer,
    )


@router.get("/me")
async def get_my_gamification_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GamificationService.get_profile(
        db=db,
        user=current_user,
    )



@router.post("/refresh-hearts")
async def refresh_hearts_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await GamificationService.refresh_hearts(
        db=db,
        user_id=current_user.id,
    )

    return {
        "message": "Hearts refreshed"
    }


@router.get("/my-badges")
async def get_user_badges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GamificationService.get_user_badges(
        db=db,
        user=current_user,
    )


@router.get("/my-gamification-progress")
async def get_level_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GamificationService.get_level_progress(
        db=db,
        user=current_user,
    )


@router.get("/my-ledger-details")
async def get_points_ledger(
    limit: int = 20,
    cursor: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GamificationService.get_points_ledger(
        db=db,
        user=user,
        limit=limit,
        cursor=cursor,
    )


