from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest,GoogleLoginRequest
from app.services.auth_service import login_user,google_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])
@router.post("/login")
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await login_user(
            db=db,
            data=payload,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    

@router.post("/google-login")
async def google_login(
    data: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await google_auth_service(
        db,
        data.id_token,
    )