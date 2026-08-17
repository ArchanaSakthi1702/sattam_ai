# app/schemas/game_level_schemas.py

from pydantic import BaseModel
from uuid import UUID

class CreateLevelRequest(BaseModel):
    level_number: int
    title: str
    topic: str | None = None
    difficulty: str
    min_exp_to_enter: int = 0
    prerequisite_level_id: UUID | None = None