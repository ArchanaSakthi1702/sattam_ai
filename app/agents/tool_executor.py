# app/agents/tool_executor.py

import logging
from datetime import datetime

from app.services.document_service import (
    DocumentService,
)
from app.services.legal_news_service import LegalNewsService
from app.services.user_profile_service import UserProfileService
logger = logging.getLogger(__name__)


class ToolExecutor:

    @staticmethod
    async def execute(
        *,
        tool_name: str,
        arguments: dict,
        db,
        user,
        session,
    ):

        logger.info(
            "Executing tool=%s session_id=%s",
            tool_name,
            session.id,
        )

        handlers = {
            "get_current_time":
                ToolExecutor.get_current_time,

            "generate_document":
                DocumentService.generate_document,

            "get_user_profile":
                UserProfileService.get_user_profile,

            "search_legal_news":
                LegalNewsService.search_news,
        }

        handler = handlers.get(tool_name)

        if not handler:

            logger.warning(
                "Unknown tool=%s session_id=%s",
                tool_name,
                session.id,
            )

            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
            }

        return await handler(
            arguments=arguments,
            db=db,
            user=user,
            session=session,
        )

    @staticmethod
    async def get_current_time(
        *,
        arguments,
        db,
        user,
        session,
    ):
        return {
            "success": True,
            "current_time": (
                datetime.utcnow()
                .isoformat()
            ),
        }