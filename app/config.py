from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str

    SECRET_KEY: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ALGORITHM:str

    REFRESH_TOKEN_EXPIRE_DAYS:int = 30

    AZURE_OPENAI_ENDPOINT: str

    CHAT_API_KEY:str

    MODEL_NAME:str="gpt-5-nano"

    DEPLOYMENT_NAME:str="gpt-5-nano"

    EMAIL_FROM:str

    RESEND_API_KEY:str

    BACKEND_URL:str

    SMTP_HOST:str = "smtp.gmail.com"
    SMTP_PORT:int = 587
    SMTP_USERNAME:str 
    SMTP_PASSWORD:str

    AZURE_STORAGE_ACCOUNT_NAME: str

    AZURE_STORAGE_ACCOUNT_KEY: str

    AZURE_STORAGE_CONNECTION_STRING:str

    AZURE_STORAGE_CONTAINER:str

    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str

    QDRANT_API_KEY:str
    QDRANT_CLUSTER_ENDPOINT:str

    AZURE_EMBEDDING_API:str
    AZURE_EMBEDDING_DEPLOYMENT:str
    AZURE_EMBEDDING_ENDPOINT:str

    GOOGLE_CLIENT_ID :str = "your-google-client-id"

    RAZOR_PAY_API_KEY:str
    RAZOR_PAY_API_SECRET:str

    AZURE_CLIENT_ID:str
    AZURE_TENANT_ID:str
    AZURE_CLIENT_SECRET:str

    
    AI_FOUNDRY_PROJECT_ENDPOINT:str

    NEWS_API_KEY:str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()