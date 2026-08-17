# app/services/chat_history_service.py

from sqlalchemy import select
import asyncio
import json
import logging
from app.helpers.openai_client import client
from app.config import get_settings

from app.schemas.history_management_schema import ChatHistoryConfig
settings = get_settings()

from app.models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class ChatHistoryService:

    MIN_MESSAGES_TO_SUMMARIZE = 3

    
    @staticmethod
    async def build_conversation(db, session: ChatSession,config: ChatHistoryConfig):

        try:
            conversation = []

            if session.summary:
                conversation.append(
                    {
                        "role": "system",
                        "content": f"""
    Previous conversation summary:

    {session.summary}
    """.strip(),
                    }
                )

            query = select(ChatMessage).where(
                ChatMessage.session_id == session.id
            )

            if session.summary_updated_at:

                query = query.where(
                    ChatMessage.created_at > session.summary_updated_at
                )

            result = await db.execute(
                query.order_by(ChatMessage.created_at.desc())
            )

            messages = result.scalars().all()
            selected = []
            current_tokens = 0

            for msg in messages:

                if (
                    selected
                    and current_tokens + msg.token_count
                    > config.history_token_budget
                ):
                    break

                selected.append(msg)
                current_tokens += msg.token_count

            selected.reverse()

            for msg in selected:
                conversation.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                    }
                )

            logger.info(
                "Conversation built successfully for session_id=%s "
                "(messages=%d, tokens=%d)",
                session.id,
                len(selected),
                current_tokens,
            )
            
            return conversation

        except Exception:
            logger.exception(
                "Failed to build conversation for session_id=%s",
                session.id,
            )
            raise

    @staticmethod
    async def summarize_if_needed(
        db,
        session: ChatSession,
        config: ChatHistoryConfig
    ):

        query = select(ChatMessage).where(
            ChatMessage.session_id == session.id
        )


        if session.summary_updated_at:

            query = query.where(
                ChatMessage.created_at > session.summary_updated_at
            )

        result = await db.execute(
            query.order_by(ChatMessage.created_at.asc())
        )

        messages = result.scalars().all()

        if not messages:
            return

        if (
            len(messages)
            < ChatHistoryService.MIN_MESSAGES_TO_SUMMARIZE
        ):
            return

        new_tokens = sum(
            m.token_count
            for m in messages
        )

        if (
            new_tokens
            < config.summary_trigger_tokens
        ):

            return

        summary_messages = []

        current_tokens = 0


        for msg in messages:

            if (
                summary_messages
                and current_tokens + msg.token_count
                > config.max_summary_input_tokens
            ):

                break

            summary_messages.append(msg)

            current_tokens += msg.token_count

        conversation_text = "\n".join(
            f"{m.role}: {m.content}"
            for m in summary_messages
        )

        current_summary = session.summary or ""

        logger.info(
            "Generating summary | session_id=%s | messages=%d | tokens=%d",
            session.id,
            len(summary_messages),
            current_tokens,
        )

        try:
            payload = [
            {
                "role": "system",
                "content": """
        You are a conversation memory compressor.

        Rules:
        - Update the existing summary
        - Preserve important facts, decisions, goals, and user preferences
        - Remove repetition, greetings, and noise
        - Maintain continuity across updates
        - Keep output structured and concise
        """
            },
            {
                "role": "user",
                "content": f"""
        Current Summary:
        {current_summary}

        New Messages:
        {conversation_text}

        Return the updated full summary.
        """
            },
        ]

            response = await asyncio.wait_for(
                client.responses.create(
                    model=settings.DEPLOYMENT_NAME,
                    input=payload,
                ),
                timeout=30,
                )

            logger.info(
                "Summary response received successfully for session_id=%s",
                session.id,
            )

        except Exception:

            logger.warning(
                "Conversation summary update failed for session_id=%s",
                session.id,
                exc_info=True,
            )

            return

        if (
            response.output_text
            and len(response.output_text) > 50
        ):

            session.summary = response.output_text

            session.summary_updated_at = (
                summary_messages[-1].created_at
            )

            logger.info(
                "Summary updated successfully for session_id=%s",
                session.id,
            )

        else:

            logger.warning(
                "Generated summary was empty or too short for session_id=%s",
                session.id,
            )

        await db.flush()