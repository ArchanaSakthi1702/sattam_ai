from azure.core.exceptions import (
    ResourceExistsError,
)

from app.config import get_settings
from app.helpers.blob_client import (
    blob_service_client,
)


settings = get_settings()


async def ensure_blob_container_exists():
    """
    Creates the Azure Blob container
    if it does not already exist.
    """

    container_client = (
        blob_service_client.get_container_client(
            settings.AZURE_STORAGE_CONTAINER
        )
    )

    try:
        await container_client.create_container()

    except ResourceExistsError:
        pass