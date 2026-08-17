from fastapi import APIRouter, Depends

from app.models import User
from app.auth.dependencies import get_current_user
from app.schemas.user_schemas import UserProfileResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserProfileResponse,
)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user