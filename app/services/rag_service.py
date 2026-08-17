from app.services.embedding_service import (
    EmbeddingService,
)
from app.models import FileChunk
from app.services.qdrant_service import (
    qdrant_client,
    QdrantService,
)

from uuid import UUID

from sqlalchemy import select
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny


class RAGService:

    @staticmethod
    async def retrieve_chunks(
        db,
        user_id,
        query: str,
        file_ids: list[str],
        limit: int = 5,
    ) -> list[str]:

        query_embedding = (
            await EmbeddingService.embed(query)
        )

        response = await qdrant_client.query_points(
            collection_name=QdrantService.COLLECTION_NAME,
            query=query_embedding,
            limit=limit,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(
                            value=str(user_id)
                        )
                    ),
                    FieldCondition(
                        key="file_id",
                        match=MatchAny(
                            any=file_ids
                        )
                    )
                ]
            )
        )

        points = response.points

        chunk_ids = [
            UUID(point.payload["chunk_id"])
            for point in points
        ]

        if not chunk_ids:
            return []

        result = await db.execute(
            select(FileChunk).where(
                FileChunk.id.in_(chunk_ids)
            )
        )

        chunks = result.scalars().all()

        chunk_map = {
            chunk.id: chunk.content
            for chunk in chunks
        }

        return [
            chunk_map[UUID(point.payload["chunk_id"])]
            for point in points
            if UUID(point.payload["chunk_id"]) in chunk_map
        ]

    @staticmethod
    async def build_rag_context(
        db,
        user_id,
        query: str,
        file_ids: list[str] | None,
    ) -> str | None:

        if not file_ids:
            return None

        chunks = await RAGService.retrieve_chunks(
            db=db,
            user_id=user_id,
            query=query,
            file_ids=file_ids,
            limit=5,
        )

        if not chunks:
            return None

        return "\n\n".join(chunks)
    

    @staticmethod
    def inject_context(
        conversation: list,
        context: str | None,
    ) -> list:

        if not context:
            return conversation

        conversation.insert(
            0,
            {
                "role": "system",
                "content": (
                    "The user has provided the following document excerpts "
                    "as additional context. Use them when they are relevant "
                    "to the user's question. If the excerpts do not contain "
                    "information relevant to the question, answer normally "
                    "using your existing knowledge and conversation context.\n\n"
                    f"{context}"
                ),
            },
        )
        return conversation