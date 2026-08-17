from azure.storage.blob.aio import BlobServiceClient

from app.config import get_settings


settings = get_settings()


blob_service_client = (
    BlobServiceClient.from_connection_string(
        settings.AZURE_STORAGE_CONNECTION_STRING
    )
)