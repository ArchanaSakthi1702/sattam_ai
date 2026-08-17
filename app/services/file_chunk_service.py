from app.models import FileChunk
from app.services.chunking_service import ChunkingService


class FileChunkService:

    @staticmethod
    async def create_chunks(
        db,
        chat_file,
        text: str,
    ) -> list[FileChunk]:

        chunks = ChunkingService.chunk_text(text)

        db_chunks = []

        for index, chunk in enumerate(chunks):

            db_chunk = FileChunk(
                file_id=chat_file.id,
                chunk_index=index,
                content=chunk,
            )

            db.add(db_chunk)

            db_chunks.append(db_chunk)

        await db.commit()

        for chunk in db_chunks:
            await db.refresh(chunk)

        return db_chunks