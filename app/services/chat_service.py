from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from uuid import UUID
import asyncio
import logging
from openai import (
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
)


from app.models import (
    ChatSession,
    ChatMessage,
    UserAIUsage,
    User,
)
from app.schemas.history_management_schema import ChatHistoryConfig
from app.services.agent_loop.agent_loop_service import AgentLoopService
from app.services.subscription_guard_service import SubscriptionGuardService
from app.services.chat_history_service import ChatHistoryService
from app.services.qdrant_service import QdrantService
from app.services.file_service import FileService
from app.services.rag_service import RAGService
from app.helpers.time_control import utc_now
from app.helpers.token_counter import count_tokens
from app.helpers.openai_client import client
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ChatService:

    @staticmethod
    async def send_message(
        db,
        user,
        message: str,
        session_id=None,
        file_ids: list[str] | None = None
    ):
        try:
            # PHASE 1
            logger.info(
                "send_message started user_id=%s session_id=%s",
                user.id,
                session_id,
            )

            if session_id:

                session = await db.scalar(
                    select(ChatSession).where(
                        ChatSession.id == session_id,
                        ChatSession.user_id == user.id,
                    )
                )

                if not session:
                    logger.warning(
                        "Chat session not found session_id=%s user_id=%s",
                        session_id,
                        user.id,
                    )
                    raise ValueError("Chat session not found")

            else:

                logger.info(
                    "Creating new chat session for user_id=%s",
                    user.id,
                )

                session = ChatSession(
                    user_id=user.id,
                    title=message[:100],
                )

                db.add(session)
                await db.flush()

                logger.info(
                    "New chat session created session_id=%s",
                    session.id,
                )

            subscription = (
                await SubscriptionGuardService.get_active_subscription(
                    db,
                    user,
                )
            )

            history_config = ChatHistoryConfig(
                history_token_budget=
                    subscription.plan.history_token_budget,

                summary_trigger_tokens=
                    subscription.plan.summary_trigger_tokens,

                max_summary_input_tokens=
                    subscription.plan.max_summary_input_tokens,
            )

            usage = (
                await SubscriptionGuardService.get_usage(
                    db,
                    user,
                )
            )


            await SubscriptionGuardService.reset_usage_if_needed(
                usage,
            )

            await SubscriptionGuardService.validate_usage_limits(
                subscription,
                usage,
            )

            db.add(
                ChatMessage(
                    session_id=session.id,
                    role="user",
                    content=message,
                    token_count=count_tokens(message),
                )
            )

            await db.commit()

            logger.info(
                "User message persisted session_id=%s",
                session.id,
            )

            # PHASE 2

            session = await db.get(
                ChatSession,
                session.id,
            )

            await ChatHistoryService.summarize_if_needed(
                db,
                session,
                history_config,
            )

            await db.commit()

            conversation = await ChatHistoryService.build_conversation(
                db,
                session,
                history_config,
            )

            logger.info(
                "Building RAG context session_id=%s file_count=%s",
                session.id,
                len(file_ids) if file_ids else 0,
            )

            rag_context = await RAGService.build_rag_context(
                db=db,
                user_id=user.id,
                query=message,
                file_ids=file_ids,
            )

            conversation = RAGService.inject_context(
                conversation,
                rag_context,
            )
            
            # PHASE 3

            logger.info(
                "Sending request to AI provider session_id=%s",
                session.id,
            )

            agent_result = await AgentLoopService.run(
                conversation=list(conversation),
                db=db,
                user=user,
                session=session,
            )
            input_tokens = agent_result["input_tokens"]
            output_tokens = agent_result["output_tokens"]
            total_tokens = agent_result["total_tokens"]

            status = agent_result["status"]
            assistant_message = agent_result["answer"]
            data = agent_result.get("data", {})
            events = agent_result.get("events",[])

            # PHASE 4

            subscription = (
                await SubscriptionGuardService.get_active_subscription(
                    db,
                    user,
                )
            )

            usage = (
                await SubscriptionGuardService.get_usage(
                    db,
                    user,
                )
            )

            await SubscriptionGuardService.reset_usage_if_needed(
                usage,
            )

            await SubscriptionGuardService.consume_tokens(
                subscription,
                usage,
                total_tokens,
            )

            db.add(
                ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=assistant_message,
                    token_count=output_tokens,
                )
            )

            session = await db.get(
                ChatSession,
                session.id,
            )
            session.updated_at = utc_now()

            await db.commit()

            logger.info(
                "send_message completed successfully session_id=%s user_id=%s",
                session.id,
                user.id,
            )
            return {
                "status": status,
                "answer": assistant_message,
                "data": data,
                "session_id": str(session.id),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "events": events,
            }
        
        except (
            RateLimitError,
            APIConnectionError,
            APITimeoutError,
            asyncio.TimeoutError,
        ) as exc:
            logger.warning(
                "AI provider call failed for user=%s session_id=%s: %s",
                user.id,
                session_id,
                exc,
            )
            await db.rollback()
            raise ValueError(
                "AI service is temporarily unavailable. Please try again."
            )

        except Exception:
            logger.exception(
                "Unexpected error in send_message for user=%s session_id=%s",
                user.id,
                session_id,
            )
            await db.rollback()
            raise


    @staticmethod
    async def get_sessions(
        db: AsyncSession,
        user: User,
        limit: int = 20,
        cursor: datetime | None = None,
    ) -> dict:

        query = (
            select(ChatSession)
            .where(
                ChatSession.user_id == user.id
            )
            .order_by(
                ChatSession.updated_at.desc()
            )
        )

        if cursor:
            query = query.where(
                ChatSession.updated_at < cursor
            )

        query = query.limit(limit + 1)

        result = await db.scalars(query)

        sessions = list(result)

        has_more = len(sessions) > limit

        if has_more:
            sessions = sessions[:limit]

        next_cursor = (
            sessions[-1].updated_at
            if has_more and sessions
            else None
        )
        logger.info(
                "Retrieved %d chat sessions for user_id=%s has_more=%s",
                len(sessions),
                user.id,
                has_more,
            )

        return {
            "items": sessions,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    

    @staticmethod
    async def get_chat_history(
        db: AsyncSession,
        user: User,
        session_id: UUID,
        limit: int = 50,
        cursor: datetime | None = None,
    ) -> dict:

        session = await db.scalar(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user.id,
            )
        )

        if not session:
            raise ValueError(
                "Chat session not found."
            )

        query = (
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id
            )
            .order_by(
                ChatMessage.created_at.desc()
            )
        )

        if cursor:
            query = query.where(
                ChatMessage.created_at < cursor
            )

        query = query.limit(limit + 1)

        result = await db.scalars(query)

        messages = list(result)

        has_more = len(messages) > limit

        if has_more:
            messages = messages[:limit]

        next_cursor = (
            messages[-1].created_at
            if has_more and messages
            else None
        )

        return {
            "items": messages,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    
    @staticmethod
    async def delete_session(
        db: AsyncSession,
        user: User,
        session_id: UUID,
    ) -> None:

        session = await db.scalar(
            select(ChatSession)
            .options(
                selectinload(ChatSession.files)
            )
            .where(
                ChatSession.id == session_id,
                ChatSession.user_id == user.id,
            )
        )

        if not session:
            raise ValueError(
                "Session not found"
            )

        for chat_file in session.files:

            await FileService.delete_from_blob(
                chat_file.file_url
            )

            await QdrantService.delete_file_points(
                str(chat_file.id)
            )

        await db.delete(session)

        await db.commit()