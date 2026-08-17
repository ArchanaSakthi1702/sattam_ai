from app.services.document_extraction_service import (
    DocumentExtractionService,
)
from app.services.file_chunk_service import (
    FileChunkService,
)
from app.services.file_embedding_service import (
    FileEmbeddingService,
)
from app.models import ChatFile

import logging

logger=logging.getLogger(__name__)


class FileProcessingService:

    @staticmethod
    async def process_file(
        db,
        chat_file: ChatFile,
        file_bytes: bytes,
        user_id,
    ):
        try:
            logger.info(
                f"Started processing file {chat_file.id}"
            )


            chat_file.processing_status = "processing"
            await db.commit()

            text = (
                await DocumentExtractionService.extract_text(
                    file_bytes
                )
            )

            logger.info(
                f"Text extracted from file {chat_file.id}"
            )

            chunks = (
                await FileChunkService.create_chunks(
                    db=db,
                    chat_file=chat_file,
                    text=text,   )
            )

            logger.info(
                f"Created {len(chunks)} chunks for file {chat_file.id}"
            )

            for chunk in chunks:

                await FileEmbeddingService.index_chunk(
                    file_chunk=chunk,
                    user_id=user_id,
                )

            chat_file.processing_status = "completed"

            await db.commit()

        except Exception:

            chat_file.processing_status = "failed"

            await db.commit()

            raise