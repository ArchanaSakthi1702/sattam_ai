from app.config import get_settings
import resend
import asyncio

from email.message import EmailMessage

import aiosmtplib

import logging

logger = logging.getLogger(__name__)

settings=get_settings()



resend.api_key = settings.RESEND_API_KEY
settings=get_settings()


async def send_verification_email(
    email: str,
    token: str,
):
    logger.info(
        "Preparing verification email | email=%s",
        email,
    )
    verification_url = (
        f"{settings.BACKEND_URL}/auth/verify-email?token={token}"
    )

    html = f"""
            <html>
            <body>
                <h2>Verify Your Email</h2>

                <p>Click below to verify your account.</p>

                <p>
                    <a href="{verification_url}">
                        Verify Email
                    </a>
                </p>

                <p>This link expires in 24 hours.</p>
            </body>
            </html> 
            """

    await send_email(
        to_email=email,
        subject="Verify your email",
        html_content=html,
    )


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
):
    try:
        logger.info(
            "Sending email | from=%s | to=%s | subject=%s",
            "onboarding@resend.dev",
            to_email,
            subject,
        )

        response = await asyncio.to_thread(
            resend.Emails.send,
            {
                "from": "onboarding@resend.dev",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            },
        )

        logger.info(
            "Email sent successfully | to=%s | subject=%s | response=%s",
            to_email,
            subject,
            response,
        )

        return response

    except Exception:
        logger.exception(
            "Failed to send email | to=%s | subject=%s",
            to_email,
            subject,
        )
        raise

async def send_password_reset_email(
    email: str,
    token: str,
):
    logger.info(
        "Preparing password reset email | email=%s",
        email,
    )

    reset_url = (
        f"{settings.BACKEND_URL}/reset-password?token={token}"
    )

    html = f"""
        <html>
        <body>
            <h2>Reset Your Password</h2>

            <p>
                We received a request to reset your password.
            </p>

            <p>
                Click the button below to create a new password.
            </p>

            <p>
                <a href="{reset_url}">
                    Reset Password
                </a>
            </p>

            <p>
                This link expires in 1 hour.
            </p>

            <p>
                If you did not request a password reset,
                you can safely ignore this email.
            </p>
        </body>
        </html>
    """

    await send_email(
        to_email=email,
        subject="Reset your password",
        html_content=html,
    )