# app/schemas/game_question_schemas.py

from pydantic import BaseModel
from uuid import UUID


class CreateQuestionRequest(BaseModel):
    order_index: int
    question_text: str
    question_type: str = "mcq"

    options: list[str] | None = None

    correct_answer: str
    explanation: str | None = None

    exp_reward: int = 10


class AnswerQuestionRequest(BaseModel):
    level_attempt_id: UUID
    answer: str