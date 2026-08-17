from app.helpers.embedding_client import client

from app.config import get_settings

settings=get_settings()


class EmbeddingService:

    @staticmethod
    async def embed(text: str) -> list[float]:

        response = await client.embeddings.create(
            model=settings.AZURE_EMBEDDING_DEPLOYMENT,
            input=text,
        )

        return response.data[0].embedding