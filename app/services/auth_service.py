from fastapi import BackgroundTasks
import logging

from sqlalchemy import select,delete
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
from datetime import timedelta
from google.auth.transport import requests
from google.oauth2 import id_token

from app.models import User,UserGamification,UserAIUsage,PasswordResetToken
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
)

from app.models import User,EmailVerificationToken
from app.schemas.auth import RegisterRequest,LoginRequest
from app.auth.password import hash_password,verify_password
from app.auth.jwt import create_access_token,create_refresh_token
from app.helpers.time_control import utc_now
from app.helpers.email_control import send_verification_email,send_password_reset_email

from app.config import get_settings

settings=get_settings()

logger = logging.getLogger(__name__)


async def register_user(
    db: AsyncSession,
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
) -> User:

    """
    Register a new user account and initiate email verification.

    This service validates that the email address is not already
    registered, creates the user record, generates an email
    verification token, and schedules a verification email to be
    sent asynchronously after successful database commit.

    Args:
        db (AsyncSession):
            Active SQLAlchemy asynchronous database session.

        data (RegisterRequest):
            User registration payload containing account and
            profile information.

        background_tasks (BackgroundTasks):
            FastAPI background task manager used to queue
            post-registration operations.

    Returns:
        User:
            The newly created user instance with persisted
            database values.

    Raises:
        ValueError:
            If the provided email address is already registered.

        Exception:
            Re-raises any unexpected exception after rolling
            back the database transaction.

    Side Effects:
        - Creates a new user record.
        - Creates an email verification token.
        - Commits database changes.
        - Queues a verification email for delivery.
        - Writes audit and operational logs.

    Notes:
        The verification token is valid for 24 hours. The
        verification email is scheduled only after a successful
        transaction commit to prevent sending emails for failed
        registrations.
    """

    logger.info(
        "User registration started | email=%s",
        data.email,
    )

    existing_user = await db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user:
        logger.warning(
            "Registration failed: email already exists | email=%s",
            data.email,
        )
        raise ValueError("Email already registered")

    try:
        user = User(
            email=data.email,
            password=hash_password(data.password),
            age=data.age,
            country=data.country,
            state=data.state,
            phone_number=data.phone_number,
            occupation_type=data.occupation_type,
            is_email_verified=False,
        )

        db.add(user)

        await db.flush()

        logger.info(
            "User record created | user_id=%s | email=%s",
            user.id,
            user.email,
        )

        token = secrets.token_urlsafe(32)

        verification = EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=utc_now() + timedelta(hours=24),
        )

        db.add(verification)

        logger.info(
            "Email verification token generated | user_id=%s",
            user.id,
        )

        await db.commit()
        await db.refresh(user)

        logger.info(
            "User registration completed | user_id=%s | email=%s",
            user.id,
            user.email,
        )

        background_tasks.add_task(
            send_verification_email,
            email=user.email,
            token=token,
        )

        logger.info(
            "Verification email queued | user_id=%s | email=%s",
            user.id,
            user.email,
        )

        return user

    except Exception:
        logger.exception(
            "Unexpected error during registration | email=%s",
            data.email,
        )
        await db.rollback()
        raise


async def login_user(
    db: AsyncSession,
    data: LoginRequest,
) -> dict:

    """
    Authenticate a user and issue JWT access and refresh tokens.

    This service validates user credentials, ensures the account
    is active and email-verified, and generates authentication
    tokens for authorized access to protected resources.

    Args:
        db (AsyncSession):
            Active SQLAlchemy asynchronous database session.

        data (LoginRequest):
            Login request containing the user's email and
            password credentials.

    Returns:
        dict:
            Authentication response containing access token,
            refresh token, token type, and basic user details.

    Raises:
        ValueError:
            Raised when:
            - The user does not exist.
            - The password is incorrect.
            - The account uses Google Sign-In.
            - Password authentication is unavailable.
            - The email address has not been verified.

        Exception:
            Any unexpected exception propagated from underlying
            authentication, database, or token generation logic.

    Side Effects:
        - Validates user credentials.
        - Generates JWT access and refresh tokens.
        - Writes authentication audit logs.

    Notes:
        Soft-deleted accounts are excluded from authentication.
        Google-authenticated users must sign in using the Google
        authentication flow and cannot use password-based login.
    """

    logger.info(
        "Login attempt | email=%s",
        data.email,
    )

    user = await db.scalar(
        select(User).where(
            User.email == data.email,
            User.is_deleted.is_(False),
        )
    )

    if not user:
        logger.warning(
            "Login failed: user not found | email=%s",
            data.email,
        )
        raise ValueError(
            "Invalid email or password"
        )

    # Google account cannot use password login
    if user.auth_provider == "google":
        logger.warning(
            "Login failed: Google account used password login | user_id=%s",
            user.id,
        )
        raise ValueError(
            "This account uses Google Sign-In. Please continue with Google."
        )

    if not user.password:
        logger.warning(
            "Login failed: password unavailable | user_id=%s",
            user.id,
        )
        raise ValueError(
            "Password login is unavailable for this account"
        )

    if not verify_password(
        data.password,
        user.password,
    ):
        logger.warning(
            "Login failed: invalid password | user_id=%s",
            user.id,
        )
        raise ValueError(
            "Invalid email or password"
        )

    if not user.is_email_verified:
        logger.warning(
            "Login failed: email not verified | user_id=%s",
            user.id,
        )
        raise ValueError(
            "Please verify your email before logging in"
        )

    logger.info(
        "Login successful | user_id=%s",
        user.id,
    )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "is_staff": user.is_staff,
        }
    )

    refresh_token = create_refresh_token(
        {
            "sub": str(user.id),
            "is_staff": user.is_staff,
        }
    )

    logger.info(
        "JWT tokens generated | user_id=%s",
        user.id,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "is_staff": user.is_staff,
            "verified_badge": user.verified_badge,
        },
    }


async def resend_verification_email_service(
    db: AsyncSession,
    email: str,
    background_tasks: BackgroundTasks,
):
    logger.info(
        "Verification email resend requested | email=%s",
        email,
    )

    try:
        user = await db.scalar(
            select(User).where(
                User.email == email,
                User.is_deleted.is_(False),
            )
        )

        if not user:
            logger.warning(
                "Verification email resend failed: user not found | email=%s",
                email,
            )
            raise ValueError("User not found")

        if user.is_email_verified:
            logger.warning(
                "Verification email resend failed: email already verified | user_id=%s",
                user.id,
            )
            raise ValueError("Email already verified")

        await db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.id
            )
        )

        logger.info(
            "Old verification tokens deleted | user_id=%s",
            user.id,
        )

        token = secrets.token_urlsafe(32)

        verification = EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=utc_now() + timedelta(hours=24),
        )

        db.add(verification)

        logger.info(
            "New verification token generated | user_id=%s",
            user.id,
        )

        await db.commit()

        logger.info(
            "Verification token saved | user_id=%s",
            user.id,
        )

        background_tasks.add_task(
            send_verification_email,
            email=user.email,
            token=token,
        )

        logger.info(
            "Verification email queued | user_id=%s",
            user.id,
        )

        return {
            "message": "Verification email sent successfully"
        }

    except ValueError:
        raise

    except Exception:
        logger.exception(
            "Verification email resend failed unexpectedly | email=%s",
            email,
        )
        await db.rollback()
        raise


async def google_auth_service(
    db: AsyncSession,
    google_token: str,
) -> dict:

    """
    Authenticate a user using Google Sign-In and issue JWT tokens.

    This service validates the Google ID token, retrieves or creates
    the associated user account, links Google credentials to an
    existing email-based account when applicable, ensures required
    user-related records exist, and generates authentication tokens
    for subsequent API access.

    Args:
        db (AsyncSession):
            Active SQLAlchemy asynchronous database session.

        google_token (str):
            Google ID token received from the client after
            successful Google authentication.

    Returns:
        dict:
            Authentication response containing access token,
            refresh token, token type, and user profile details.

    Raises:
        ValueError:
            Raised when the provided Google token is invalid
            or cannot be verified.

        Exception:
            Re-raises unexpected exceptions after rolling back
            the database transaction.

    Side Effects:
        - Verifies the Google ID token.
        - Creates a new user account for first-time Google users.
        - Links Google credentials to existing accounts.
        - Automatically verifies the user's email address.
        - Creates required user-related records when missing.
        - Generates JWT access and refresh tokens.
        - Commits database changes.
        - Writes authentication and audit logs.

    Notes:
        Google-authenticated users are automatically marked as
        email verified because verification is handled by Google.
        Existing email-based accounts sharing the same email
        address can be linked to a Google account during login.
    """

    logger.info("Google authentication attempt")

    try:
        payload = id_token.verify_oauth2_token(
            google_token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

        email = payload["email"]
        google_id = payload["sub"]

        logger.info(
            "Google token verified | email=%s",
            email,
        )

        user = await db.scalar(
            select(User).where(
                User.email == email,
                User.is_deleted.is_(False),
            )
        )

        # Register user if not exists
        if not user:

            logger.info(
                "Creating new Google user | email=%s",
                email,
            )

            user = User(
                email=email,
                google_id=google_id,
                auth_provider="google",
                is_email_verified=True,
                email_verified_at=utc_now(),
            )

            db.add(user)

            # Generate UUID before creating related records
            await db.flush()

            logger.info(
                "Google user record created | user_id=%s",
                user.id,
            )

            db.add_all(
                [
                    UserGamification(
                        user_id=user.id,
                    ),
                    UserAIUsage(
                        user_id=user.id,
                    ),
                ]
            )

            await db.commit()
            await db.refresh(user)

            logger.info(
                "Google user registered successfully | user_id=%s",
                user.id,
            )

        else:

            logger.info(
                "Existing user found for Google login | user_id=%s",
                user.id,
            )

            # Link Google account if existing email user
            if not user.google_id:
                user.google_id = google_id

                logger.info(
                    "Google account linked to existing user | user_id=%s",
                    user.id,
                )

            user.is_email_verified = True

            if not user.email_verified_at:
                user.email_verified_at = utc_now()

            await db.commit()
            await db.refresh(user)

            logger.info(
                "Google user updated successfully | user_id=%s",
                user.id,
            )

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

        access_token = create_access_token(
            {
                "sub": str(user.id),
                "is_staff": user.is_staff,
            }
        )

        refresh_token = create_refresh_token(
            {
                "sub": str(user.id),
                "is_staff": user.is_staff,
            }
        )

        logger.info(
            "Google login successful | user_id=%s",
            user.id,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "is_staff": user.is_staff,
                "verified_badge": user.verified_badge,
                "is_email_verified": user.is_email_verified,
            },
        }

    except ValueError:
        logger.warning("Invalid Google token received")
        raise

    except Exception:
        logger.exception(
            "Google authentication failed unexpectedly"
        )
        await db.rollback()
        raise



async def forgot_password(
    db: AsyncSession,
    email: str,
    background_tasks: BackgroundTasks,
):

    """
    Initiate the password reset workflow for a user account.

    This service generates a temporary password reset token,
    invalidates any existing reset tokens for the user, and
    schedules a password reset email to be sent asynchronously.

    Args:
        db (AsyncSession):
            Active SQLAlchemy asynchronous database session.

        email (str):
            Email address associated with the account requesting
            a password reset.

        background_tasks (BackgroundTasks):
            FastAPI background task manager used to queue
            email delivery operations.

    Returns:
        None:
            The service does not return any value. Requests for
            non-existent accounts are silently ignored to prevent
            user enumeration.

    Raises:
        Exception:
            Re-raises unexpected exceptions after rolling back
            the database transaction.

    Side Effects:
        - Removes existing password reset tokens for the user.
        - Creates a new password reset token.
        - Persists reset token data to the database.
        - Queues a password reset email for delivery.
        - Writes security and operational logs.

    Security:
        The service intentionally does not disclose whether an
        email address is associated with an account, reducing
        the risk of user enumeration attacks.

    Notes:
        Password reset tokens expire one hour after creation.
        Any previously issued reset tokens for the same user are
        invalidated before a new token is generated.
    """

    logger.info(
        "Password reset requested | email=%s",
        email,
    )

    try:
        user = await db.scalar(
            select(User).where(
                User.email == email,
                User.is_deleted.is_(False),
            )
        )

        # Do not reveal whether the email exists
        if not user:
            logger.info(
                "Password reset requested for non-existent account"
            )
            return

        token = secrets.token_urlsafe(32)

        await db.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id
            )
        )

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=utc_now() + timedelta(hours=1),
        )

        db.add(reset_token)

        logger.info(
            "Password reset token created | user_id=%s",
            user.id,
        )

        await db.commit()

        logger.info(
            "Password reset token saved | user_id=%s",
            user.id,
        )

        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            token,
        )

        logger.info(
            "Password reset email queued | user_id=%s",
            user.id,
        )

    except Exception:
        logger.exception(
            "Password reset request failed | email=%s",
            email,
        )
        await db.rollback()
        raise


@staticmethod
async def reset_password(
    db: AsyncSession,
    token: str,
    new_password: str,
):

    """
    Reset a user's password using a valid password reset token.

    This service validates the provided reset token, verifies
    that it has not expired, updates the user's password, and
    invalidates the token to prevent reuse.

    Args:
        db (AsyncSession):
            Active SQLAlchemy asynchronous database session.

        token (str):
            Password reset token issued during the password
            recovery process.

        new_password (str):
            New password to be securely hashed and stored for
            the user account.

    Returns:
        None:
            The password is updated successfully without
            returning a value.

    Raises:
        ValueError:
            Raised when:
            - The reset token is invalid.
            - The reset token has expired.
            - The associated user account cannot be found.

        Exception:
            Re-raises unexpected exceptions after rolling back
            the database transaction.

    Side Effects:
        - Updates the user's password hash.
        - Deletes the password reset token.
        - Commits database changes.
        - Writes security and audit logs.

    Security:
        Passwords are never stored in plain text and are
        securely hashed before persistence. Reset tokens are
        invalidated immediately after successful password
        changes to prevent replay attacks.

    Notes:
        A password reset token can only be used once and must
        be valid at the time of the reset request.
    """
    
    logger.info(
        "Password reset attempt"
    )

    try:
        reset_token = await db.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.token == token
            )
        )

        if not reset_token:
            logger.warning(
                "Password reset failed: invalid token"
            )
            raise ValueError(
                "Invalid reset token"
            )

        if reset_token.expires_at < utc_now():
            logger.warning(
                "Password reset failed: expired token"
            )
            raise ValueError(
                "Reset token expired"
            )

        user = await db.get(
            User,
            reset_token.user_id,
        )

        if not user:
            logger.warning(
                "Password reset failed: user not found"
            )
            raise ValueError(
                "User not found"
            )

        logger.info(
            "Updating password | user_id=%s",
            user.id,
        )

        user.password = hash_password(
            new_password
        )

        await db.delete(reset_token)

        logger.info(
            "Password reset token deleted | user_id=%s",
            user.id,
        )

        await db.commit()

        logger.info(
            "Password reset successful | user_id=%s",
            user.id,
        )

    except ValueError:
        raise

    except Exception:
        logger.exception(
            "Unexpected error during password reset"
        )
        await db.rollback()
        raise