from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.qdrant_service import (
    QdrantService,
)


class FileEmbeddingService:

    @staticmethod
    async def index_chunk(
        file_chunk,
        user_id,
    ):

        embedding = await EmbeddingService.embed(
            file_chunk.content
        )

        await QdrantService.upsert_point(
            point_id=str(file_chunk.id),
            vector=embedding,
            payload={
                "file_id": str(file_chunk.file_id),
                "chunk_id": str(file_chunk.id),
                "user_id": str(user_id),
            },
        )