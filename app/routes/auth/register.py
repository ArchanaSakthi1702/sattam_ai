# api/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException,BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
async def register(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await register_user(
            db=db,
            data=payload,
            background_tasks=background_tasks,
        )

        return {
            "id": str(user.id),
            "email": user.email,
            "message": "Registration successful",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )