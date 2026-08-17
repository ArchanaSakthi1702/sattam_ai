# app/services/user_profile_service.py

import logging

logger = logging.getLogger(__name__)


class UserProfileService:

    @staticmethod
    async def get_user_profile(
        *,
        arguments,
        db,
        user,
        session,
    ):

        logger.info(
            "Fetching user profile user_id=%s",
            user.id,
        )

        return {
            "status": "completed",
            "message": "User profile retrieved successfully.",
            "data": {
                "profile": {
                    "id": str(user.id),
                    "email": user.email,
                    "auth_provider": user.auth_provider,
                    "is_active": user.is_active,
                    "is_email_verified": (
                        user.is_email_verified
                    ),
                    "verified_badge": (
                        user.verified_badge
                    ),
                    "verified_type": (
                        user.verified_type
                    ),
                    "age": user.age,
                    "country": user.country,
                    "state": user.state,
                    "phone_number": (
                        user.phone_number
                    ),
                    "occupation_type": (
                        user.occupation_type
                    ),
                    "experience_level": (
                        user.experience_level
                    ),
                    "created_at": (
                        user.created_at.isoformat()
                        if user.created_at
                        else None
                    ),
                }
            },
        }