from openai import AsyncAzureOpenAI

from app.config import get_settings

settings = get_settings()


client = AsyncAzureOpenAI(
    azure_endpoint=settings.AZURE_EMBEDDING_ENDPOINT,
    api_key=settings.AZURE_EMBEDDING_API,
    api_version="2024-02-01",
)