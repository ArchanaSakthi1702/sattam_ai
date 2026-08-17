import uuid

from fastapi import UploadFile,BackgroundTasks,HTTPException,status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from urllib.parse import urlparse

from app.models import ChatFile,User
from app.services.subscription_guard_service import (
    SubscriptionGuardService,
)
from app.services.file_guard_service import (
    FileGuardService,
)
from app.services.qdrant_service import QdrantService

from app.helpers.blob_client import (
    blob_service_client,
)

from app.background_tasks import process_uploaded_file
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()


class FileService:

    @staticmethod
    async def upload_file(
        db,
        user,
        session_id,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ):

        logger.info(
            "File upload started user_id=%s session_id=%s filename=%s",
            user.id,
            session_id,
            file.filename,
        )
        subscription = (
            await SubscriptionGuardService
            .get_active_subscription(
                db,
                user,
            )
        )

        content = await file.read()

        file_size = len(content)

        logger.debug(
            "File size calculated user_id=%s filename=%s size_bytes=%s",
            user.id,
            file.filename,
            file_size,
        )

        await FileGuardService.validate_file_upload(
            db=db,
            user=user,
            subscription=subscription,
            file_size_bytes=file_size,
        )

        logger.info(
            "File validation passed user_id=%s filename=%s",
            user.id,
            file.filename,
        )

        blob_name = (
            f"{user.id}/"
            f"{uuid.uuid4()}_"
            f"{file.filename}"
        )

        logger.info(
            "Uploading file to blob storage user_id=%s blob_name=%s",
            user.id,
            blob_name,
        )
        file_url = await FileService.upload_to_blob(
            blob_name=blob_name,
            content=content,
        )

        logger.info(
            "Blob upload successful user_id=%s blob_name=%s",
            user.id,
            blob_name,
        )
        chat_file = ChatFile(
            user_id=user.id,
            session_id=session_id,
            filename=file.filename,
            file_size=file_size,
            file_url=file_url,
        )

        db.add(chat_file)

        await db.commit()
        await db.refresh(chat_file)
        logger.info(
            "File record created file_id=%s user_id=%s",
            chat_file.id,
            user.id,
        )

        background_tasks.add_task(
            process_uploaded_file,
            chat_file.id,
            content,
            user.id,
        )

        logger.info(
            "File processing task queued file_id=%s user_id=%s",
            chat_file.id,
            user.id,
        )

        return {
            "id": str(chat_file.id),
            "filename": chat_file.filename,
            "url": chat_file.file_url,
        }
    
    
    @staticmethod
    async def upload_to_blob(
        blob_name: str,
        content: bytes,
    ) -> str:

        logger.debug(
            "Starting Azure blob upload blob_name=%s size_bytes=%s",
            blob_name,
            len(content),
        )

        blob_client = (
            blob_service_client
            .get_blob_client(
                container=settings.AZURE_STORAGE_CONTAINER,
                blob=blob_name,
            )
        )

        await blob_client.upload_blob(
            content,
            overwrite=True,
        )

        logger.info(
            "Azure blob upload completed blob_name=%s",
            blob_name,
        )

        return blob_client.url
    

    @staticmethod
    async def get_files(
        db: AsyncSession,
        user: User,
        limit: int = 20,
        cursor: datetime | None = None,
    ) -> dict:

        query = (
            select(ChatFile)
            .where(
                ChatFile.user_id == user.id
            )
            .order_by(
                ChatFile.uploaded_at.desc()
            )
        )

        if cursor:
            query = query.where(
                ChatFile.uploaded_at < cursor
            )

        query = query.limit(limit + 1)

        result = await db.scalars(query)

        files = list(result)

        has_more = len(files) > limit

        if has_more:
            files = files[:limit]

        next_cursor = (
            files[-1].uploaded_at
            if has_more and files
            else None
        )

        return {
            "items": files,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    


    @staticmethod
    async def delete_file(
        db,
        user,
        file_id,
    ):

        chat_file = await db.scalar(
            select(ChatFile).where(
                ChatFile.id == file_id,
                ChatFile.user_id == user.id,
            )
        )

        if not chat_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        await FileService.delete_from_blob(
            chat_file.file_url
        )

        await QdrantService.delete_file_points(
            str(chat_file.id)
        )

        await db.delete(chat_file)

        await db.commit()



    @staticmethod
    async def delete_from_blob(
        file_url: str,
    ):

        parsed = urlparse(file_url)

        blob_name = (
            parsed.path
            .split("/", 2)[2]
        )

        blob_client = (
            blob_service_client.get_blob_client(
                container=settings.AZURE_STORAGE_CONTAINER,
                blob=blob_name,
            )
        )

        await blob_client.delete_blob()