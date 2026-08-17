from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession


from app.database import get_db
from app.models import User
from app.schemas.auth import RefreshTokenRequest
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_refresh_user


router=APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/refresh")
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_refresh_user(
        refresh_token=data.refresh_token,
        db=db,
    )

    access_token = create_access_token(
        {
            "sub": str(current_user.id),
            "is_staff": current_user.is_staff,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }