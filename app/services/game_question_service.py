# app/services/game_question_service.py

from uuid import UUID

from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    GameLevel,
    GameQuestion,
    User,LevelAttempt,UserQuestionAttempt,UserGamification,UserQuestionEXP,PointsLedgerEntry,UserLevelProgress
)
from app.services.gamification_service import GamificationService
from app.helpers.time_control import utc_now


class GameQuestionService:

    @staticmethod
    async def create_question(
        db: AsyncSession,
        level_id: UUID,
        order_index: int,
        question_text: str,
        question_type: str,
        options: list[str] | None,
        correct_answer: str,
        explanation: str | None,
        exp_reward: int,
    ):
        level = await db.get(
            GameLevel,
            level_id,
        )

        if not level:
            raise ValueError(
                "Level not found."
            )

        existing_question = await db.scalar(
            select(GameQuestion).where(
                GameQuestion.level_id == level_id,
                GameQuestion.order_index == order_index,
            )
        )

        if existing_question:
            raise ValueError(
                f"Question order {order_index} already exists in this level."
            )

        allowed_types = {
            "mcq",
            "true_false",
            "short_answer",
        }

        if question_type not in allowed_types:
            raise ValueError(
                f"Invalid question type. Allowed values: {', '.join(allowed_types)}"
            )

        if question_type == "mcq":
            if not options or len(options) < 2:
                raise ValueError(
                    "MCQ questions require at least 2 options."
                )

            if correct_answer not in options:
                raise ValueError(
                    "Correct answer must exist in options."
                )

        question = GameQuestion(
            level_id=level_id,
            order_index=order_index,
            question_text=question_text,
            question_type=question_type,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            exp_reward=exp_reward,
        )

        db.add(question)

        await db.commit()
        await db.refresh(question)

        return {
            "id": question.id,
            "level_id": question.level_id,
            "order_index": question.order_index,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "options": question.options,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "exp_reward": question.exp_reward,
            "created_at": question.created_at,
        }
    

    from sqlalchemy import select

    @staticmethod
    async def answer_question(
        db: AsyncSession,
        user: User,
        question_id: UUID,
        level_attempt_id: UUID,
        answer: str,
    ) -> dict:

        attempt = await db.get(
            LevelAttempt,
            level_attempt_id,
        )

        if not attempt:
            raise ValueError("Attempt not found")

        if attempt.user_id != user.id:
            raise ValueError("Invalid attempt")

        if attempt.is_completed:
            raise ValueError(
                "Level already completed"
            )

        question = await db.get(
            GameQuestion,
            question_id,
        )

        if not question:
            raise ValueError(
                "Question not found"
            )

        if question.level_id != attempt.level_id:
            raise ValueError(
                "Question does not belong to this level"
            )

        existing_attempt = await db.scalar(
            select(UserQuestionAttempt).where(
                UserQuestionAttempt.level_attempt_id
                == attempt.id,
                UserQuestionAttempt.question_id
                == question.id,
            )
        )

        if existing_attempt:
            raise ValueError(
                "Question already answered"
            )

        gamification = await db.get(
            UserGamification,
            user.id,
        )

        if not gamification:
            raise ValueError(
                "Gamification profile not found"
            )
        
        await GamificationService.refresh_hearts(
            db=db,
            user_id=user.id,
        )

        await db.refresh(gamification)

        if gamification.hearts_current <= 0:
            raise ValueError(
                "No hearts remaining"
            )

        is_correct = (
            answer.strip().lower()
            ==
            question.correct_answer.strip().lower()
        )

        exp_awarded = 0

        if is_correct:

            already_claimed = await db.get(
                UserQuestionEXP,
                (user.id, question.id),
            )

            if not already_claimed:

                exp_awarded = question.exp_reward

                gamification.total_exp += exp_awarded

                db.add(
                    UserQuestionEXP(
                        user_id=user.id,
                        question_id=question.id,
                        exp_awarded=exp_awarded,
                    )
                )

                db.add(
                    PointsLedgerEntry(
                        user_id=user.id,
                        points=exp_awarded,
                        reason="question_correct",
                        meta=(
                            f'{{"question_id":"{question.id}"}}'
                        ),
                    )
                )

            attempt.correct_answers += 1
            attempt.exp_earned += exp_awarded

        else:

            gamification.hearts_current = max(
                0,
                gamification.hearts_current - 1,
            )

            attempt.wrong_answers += 1
            attempt.hearts_lost += 1

        db.add(
            UserQuestionAttempt(
                user_id=user.id,
                question_id=question.id,
                level_attempt_id=attempt.id,
                submitted_answer=answer,
                is_correct=is_correct,
                exp_awarded=exp_awarded,
            )
        )

        total_questions = await db.scalar(
            select(func.count(GameQuestion.id))
            .where(
                GameQuestion.level_id == attempt.level_id
            )
        )

        answered_questions = await db.scalar(
            select(func.count(UserQuestionAttempt.id))
            .where(
                UserQuestionAttempt.level_attempt_id
                == attempt.id
            )
        )

        level_completed = (
            answered_questions + 1
            >= total_questions
        )

        if level_completed:

            attempt.is_completed = True
            attempt.completed_at = utc_now()

            progress = await db.scalar(
                select(UserLevelProgress)
                .where(
                    UserLevelProgress.user_id == user.id,
                    UserLevelProgress.level_id == attempt.level_id,
                )
            )

            if progress:

                progress.times_completed += 1

                if not progress.first_completed_at:
                    progress.first_completed_at = utc_now()

            if attempt.wrong_answers == 0:

                attempt.is_perfect = True

                if progress:
                    progress.times_perfect += 1

                gamification.winning_streak += 1

                gamification.longest_winning_streak = max(
                    gamification.longest_winning_streak,
                    gamification.winning_streak,
                )

            else:

                gamification.winning_streak = 0

        await db.commit()

        return {
            "question_id": question.id,
            "correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "exp_awarded": exp_awarded,
            "total_exp": gamification.total_exp,
            "hearts_remaining": gamification.hearts_current,
            "attempt_correct_answers": attempt.correct_answers,
            "attempt_wrong_answers": attempt.wrong_answers,
        }