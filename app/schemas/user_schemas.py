# app/schemas/user/profile.py

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel,ConfigDict


class UserProfileResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool
    is_staff: bool
    verified_badge: bool
    verified_type: str | None
    age: int | None
    country: str | None
    state: str | None
    phone_number: int | None
    occupation_type: str | None
    experience_level: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
