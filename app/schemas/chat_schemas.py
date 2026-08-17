from pydantic import BaseModel
from uuid import UUID


class ChatRequest(BaseModel):
    session_id: UUID | None = None
    message: str
    file_ids: list[str] | None = None