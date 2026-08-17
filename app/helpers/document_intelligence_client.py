from azure.core.credentials import (
    AzureKeyCredential,
)

from azure.ai.documentintelligence.aio import (
    DocumentIntelligenceClient,
)

from app.config import get_settings


settings = get_settings()

document_client = (
    DocumentIntelligenceClient(
        endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
        credential=AzureKeyCredential(
            settings.AZURE_DOCUMENT_INTELLIGENCE_KEY
        ),
    )
)