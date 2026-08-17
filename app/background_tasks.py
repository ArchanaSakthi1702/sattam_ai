from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import ChatFile
from app.services.file_processing_service import (
    FileProcessingService,
)


async def process_uploaded_file(
    file_id,
    file_bytes,
    user_id,
):

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(ChatFile).where(
                ChatFile.id == file_id
            )
        )

        chat_file = result.scalar_one()

        await FileProcessingService.process_file(
            db=db,
            chat_file=chat_file,
            file_bytes=file_bytes,
            user_id=user_id,
        )