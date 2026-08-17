from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct
)

from app.config import get_settings


settings = get_settings()


qdrant_client = AsyncQdrantClient(
    url=settings.QDRANT_CLUSTER_ENDPOINT,
    api_key=settings.QDRANT_API_KEY,
)


class QdrantService:

    COLLECTION_NAME = "file_chunks"

    @staticmethod
    async def upsert_point(
        point_id: str,
        vector: list[float],
        payload: dict,
    ):

        await qdrant_client.upsert(
            collection_name=QdrantService.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )


    @staticmethod
    async def delete_file_points(
        file_id: str,
    ):

        await qdrant_client.delete(
            collection_name=(
                QdrantService.COLLECTION_NAME
            ),
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="file_id",
                        match=MatchValue(
                            value=file_id
                        ),
                    )
                ]
            ),
        )