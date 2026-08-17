from fastapi import APIRouter, Depends, HTTPException,BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmailVerificationToken,User,UserGamification
from app.schemas.auth import ResendVerificationRequest,ForgotPasswordRequest,ResetPasswordRequest
from app.database import get_db
from app.helpers.time_control import utc_now
from app.services.auth_service import resend_verification_email_service,forgot_password,reset_password


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
    )


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    verification = await db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token == token
        )
    )

    if not verification:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification token",
        )

    if verification.expires_at < utc_now():
        raise HTTPException(
            status_code=400,
            detail="Verification token expired",
        )

    user = await db.get(
        User,
        verification.user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    user.is_email_verified = True
    user.email_verified_at = utc_now()

    gamification = await db.get(
        UserGamification,
        user.id,
    )

    if not gamification:
        db.add(
            UserGamification(
                user_id=user.id,
            )
        )

    await db.delete(verification)

    await db.commit()

    return {
        "message": "Email verified successfully"
    }


@router.post("/resend-verification-email")
async def resend_verification_email(
    payload: ResendVerificationRequest,
    background_tasks:BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await resend_verification_email_service(
            db=db,
            email=payload.email,
            background_tasks=background_tasks
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    

@router.post("/forgot-password")
async def forgot_password_endpoint(
    payload: ForgotPasswordRequest,
    background_tasks:BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    await forgot_password(
        db=db,
        email=payload.email,
        background_tasks=background_tasks,
    )

    return {
        "message":
        "If the email exists, a reset link has been sent"
    }


@router.post("/reset-password")
async def reset_password_endpoint(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        await reset_password(
            db=db,
            token=payload.token,
            new_password=payload.new_password,
        )

        return {
            "message":
            "Password reset successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )