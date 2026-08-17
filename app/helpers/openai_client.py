from azure.identity.aio import ClientSecretCredential
from azure.ai.projects.aio import AIProjectClient

from app.config import get_settings
settings = get_settings()


credential = ClientSecretCredential(
    tenant_id=settings.AZURE_TENANT_ID,
    client_id=settings.AZURE_CLIENT_ID,
    client_secret=settings.AZURE_CLIENT_SECRET,
)

project_client = AIProjectClient(
    endpoint=settings.AI_FOUNDRY_PROJECT_ENDPOINT,
    credential=credential,
)

client = project_client.get_openai_client()