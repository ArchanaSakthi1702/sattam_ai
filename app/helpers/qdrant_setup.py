from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


class QdrantSetup:

    def __init__(self, url: str, api_key: str):
        self.client = QdrantClient(
            url=url,
            api_key=api_key
        )

    def create_collection(self, collection_name: str, vector_size: int = 1536):
        """
        vector_size:
            - 1536 → text-embedding-3-small (OpenAI)
            - 3072 → text-embedding-3-large
        """

        collections = self.client.get_collections().collections
        existing = [c.name for c in collections]

        if collection_name in existing:
            print("Collection already exists")
            return

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

        print(f"Collection '{collection_name}' created successfully")