from __future__ import annotations


from sqlalchemy import (
    String,
    Boolean,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    Index,
    Numeric,
    text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
import uuid
from datetime import date, datetime

from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base
from app.helpers.time_control import utc_now


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    password: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    google_id: Mapped[str | None] = mapped_column(
        String,
        unique=True,
        nullable=True,
        index=True,
    )

    auth_provider: Mapped[str] = mapped_column(
        String,
        default="email",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    is_staff: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    verified_badge: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    verified_type: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    phone_number: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
        index=True,
    )

    occupation_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    experience_level: Mapped[str] = mapped_column(
        String,
        default="beginner",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    subscription: Mapped["UserSubscription"] = relationship(
        back_populates="user"
    )

    ai_usage: Mapped["UserAIUsage"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    gamification: Mapped["UserGamification"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    payments: Mapped[list["Payment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    token: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    token: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )


class UserAIUsage(Base):
    __tablename__ = "user_ai_usage"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    daily_tokens_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    monthly_tokens_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    last_daily_reset: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    last_monthly_reset: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    user: Mapped["User"] = relationship(
        back_populates="ai_usage",
    )



class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    title: Mapped[str] = mapped_column(
        String,
        default="Session",
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    summary_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    user: Mapped["User"] = relationship(
        back_populates="chat_sessions",
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    files: Mapped[list["ChatFile"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
            Index(
                "ix_chat_sessions_user_updated",
                "user_id",
                "updated_at",
            ),
        )



class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
    )

    role: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    token_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    session: Mapped["ChatSession"] = relationship(
        back_populates="messages",
    )

    __table_args__ = (
        Index(
            "ix_chat_messages_session_created",
            "session_id",
            "created_at",
        ),
    )


class ChatFile(Base):
    __tablename__ = "chat_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )

    filename: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    file_url: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    processing_status: Mapped[str] = mapped_column(
        String,
        default="uploaded",
        nullable=False,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    session: Mapped["ChatSession | None"] = relationship(
        back_populates="files",
    )

    chunks: Mapped[list["FileChunk"]] = relationship(
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_chat_files_user_uploaded",
            "user_id",
            "uploaded_at",
        ),
    )


class FileChunk(Base):
    __tablename__ = "file_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "chat_files.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    file: Mapped["ChatFile"] = relationship(
        back_populates="chunks",
    )

    __table_args__ = (
        UniqueConstraint(
            "file_id",
            "chunk_index",
            name="uq_file_chunk_order",
        ),
    )


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    daily_ai_limit: Mapped[int] = mapped_column(
        Integer,
        default=10000,
    )

    monthly_ai_limit: Mapped[int] = mapped_column(
        Integer,
        default=300000,
    )

    max_storage_mb: Mapped[int] = mapped_column(
        Integer,
        default=100,
    )

    max_files: Mapped[int] = mapped_column(
        Integer,
        default=10,
    )

    price: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    history_token_budget: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("10000"),
    )

    summary_trigger_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("5000"),
    )

    max_summary_input_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("3000"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    users: Mapped[list["UserSubscription"]] = relationship(
        back_populates="plan",
    )

    payments: Mapped[list["Payment"]] = relationship(
        back_populates="plan",
    )



class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id"),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="subscription",
    )

    plan: Mapped["SubscriptionPlan"] = relationship(
        back_populates="users",
    )

    __table_args__ = (
        Index(
            "uq_user_one_active_subscription",
            "user_id",
            unique=True,
            postgresql_where=(is_active.is_(True)),
        ),
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id"),
        nullable=False,
    )

    razorpay_order_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    razorpay_signature: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="created",
        nullable=False,
    )
    # created, paid, failed, refunded

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="payments",
    )

    plan: Mapped["SubscriptionPlan"] = relationship(
        back_populates="payments",
    )

    __table_args__ = (
        Index(
            "ix_payment_order_status",
            "razorpay_order_id",
            "status",
        ),
    )



# =============================================================================
# 1. CORE STATE — one row per user, holds every live gamification stat.
# =============================================================================
class UserGamification(Base):
    __tablename__ = "user_gamification"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # --- EXP & account level -------------------------------------------------
    total_exp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # --- hearts (global, regenerating) ---------------------------------------
    hearts_current: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
    )

    hearts_max: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
    )

    # elapsed_seconds = now - last_heart_regen_at
    # hearts_to_add = elapsed_seconds // 300  (1 heart / 5 min)
    # hearts_current = min(hearts_max, hearts_current + hearts_to_add)
    # advance last_heart_regen_at by (hearts_to_add * 300s), not to `now`
    last_heart_regen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # --- winning streak (perfect levels in a row) ----------------------------
    winning_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    longest_winning_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # --- daily login streak (separate axis — just showing up) ---------------
    login_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    longest_login_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    last_active_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # --- opt-in for firm/team leaderboard visibility -------------------------
    leaderboard_opt_in: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    # --- relationships ---------------------------------------------------
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="gamification",
    )

    badges: Mapped[list["UserBadge"]] = relationship(
        back_populates="user_gamification",
        cascade="all, delete-orphan",
    )

    points_log: Mapped[list["PointsLedgerEntry"]] = relationship(
        back_populates="user_gamification",
        cascade="all, delete-orphan",
        order_by="PointsLedgerEntry.created_at.desc()",
    )

    level_progress: Mapped[list["UserLevelProgress"]] = relationship(
        back_populates="user_gamification",
        cascade="all, delete-orphan",
    )

    question_exp: Mapped[list["UserQuestionEXP"]] = relationship(
        back_populates="user_gamification",
        cascade="all, delete-orphan",
    )

    level_attempts: Mapped[list["LevelAttempt"]] = relationship(
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_gamification_total_exp",
            "total_exp",
        ),
    )


# =============================================================================
# 2. ACCOUNT LEVEL LOOKUP — total_exp maps to a level number + title.
#    Data-driven so the curve/titles can change without code changes.
# =============================================================================
class AccountLevel(Base):
    __tablename__ = "account_levels"

    level_number: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # e.g. "Contract Fundamentals"

    exp_required: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    icon_url: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )


# =============================================================================
# 3. BADGES — catalog + earned join table
# =============================================================================
class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    icon_url: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    criteria_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    # "login_streak" | "winning_streak" | "total_exp" |
    # "levels_perfect" | "chat_sessions" | "files_reviewed" | "custom"

    criteria_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    earned_by: Mapped[list["UserBadge"]] = relationship(
        back_populates="badge",
    )


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_gamification.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    badge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False,
    )

    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    user_gamification: Mapped["UserGamification"] = relationship(
        back_populates="badges",
    )

    badge: Mapped["Badge"] = relationship(
        back_populates="earned_by",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge_once"),
        Index(
            "ix_user_badges_user",
            "user_id",
        )
    )



# =============================================================================
# 4. POINTS/EXP LEDGER — append-only audit trail for every EXP event
#    (question correct, streak bonus, real product usage, etc).
# =============================================================================
class PointsLedgerEntry(Base):
    __tablename__ = "points_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_gamification.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    # "question_correct" | "streak_bonus" | "daily_login" |
    # "document_reviewed" | "case_summary_completed" | ...

    meta: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )  # optional JSON string, e.g. {"question_id": "...", "level_id": "..."}

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    user_gamification: Mapped["UserGamification"] = relationship(
        back_populates="points_log",
    )

    __table_args__ = (
        Index("ix_points_ledger_user_created", "user_id", "created_at"),
    )


# =============================================================================
# 5. LEARNING GAME — levels, questions, per-question EXP claims
# =============================================================================
class GameLevel(Base):
    __tablename__ = "game_levels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    level_number: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    topic: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    difficulty: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # "easy" | "medium" | "hard" | "expert"

    # EXP-gated entry — not strict sequence. User can enter any level
    # whose threshold their total_exp has cleared.
    min_exp_to_enter: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # optional hard prerequisite for topics that genuinely depend on
    # earlier material, independent of raw EXP
    prerequisite_level_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game_levels.id"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    questions: Mapped[list["GameQuestion"]] = relationship(
        back_populates="level",
        cascade="all, delete-orphan",
        order_by="GameQuestion.order_index",
        foreign_keys="GameQuestion.level_id",
    )

    progress: Mapped[list["UserLevelProgress"]] = relationship(
        back_populates="level",
    )


class GameQuestion(Base):
    __tablename__ = "game_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game_levels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    question_type: Mapped[str] = mapped_column(
        String(20),
        default="mcq",
        nullable=False,
    )  # "mcq" | "true_false" | "short_answer"

    options: Mapped[dict | list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    correct_answer: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # EXP lives per-question, not per-level — this is what makes
    # "replay only pays for previously-wrong questions" possible.
    exp_reward: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    level: Mapped["GameLevel"] = relationship(
        back_populates="questions",
        foreign_keys=[level_id],
    )

    __table_args__ = (
        UniqueConstraint("level_id", "order_index", name="uq_level_question_order"),
    )


class UserLevelProgress(Base):
    """Aggregate per-(user, level) history. Replay is unrestricted, hearts
    are global — so this just tracks stats, not in-progress state."""

    __tablename__ = "user_level_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_gamification.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game_levels.id", ondelete="CASCADE"),
        nullable=False,
    )

    times_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    times_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    times_perfect: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    first_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_played_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    user_gamification: Mapped["UserGamification"] = relationship(
        back_populates="level_progress",
    )

    level: Mapped["GameLevel"] = relationship(
        back_populates="progress",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "level_id", name="uq_user_level_progress"),
        Index(
            "ix_progress_user",
            "user_id",
        )
    )


class UserQuestionAttempt(Base):
    """Full history of every answer ever submitted."""

    __tablename__ = "user_question_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_gamification.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game_questions.id", ondelete="CASCADE"),
        nullable=False,
    )


    level_attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "level_attempts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    submitted_answer: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    exp_awarded: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )  # 0 if wrong, or correct-but-already-claimed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    __table_args__ = (
        Index(
            "ix_attempt_user_question",
            "user_id",
            "question_id",
        ),
        Index(
            "ix_attempt_level_attempt",
            "level_attempt_id",
        ),
    )


class UserQuestionEXP(Base):
    """Existence of a row = this user has claimed EXP for this question,
    ever. Enforces one-time EXP per question regardless of replays."""

    __tablename__ = "user_question_exp"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_gamification.user_id", ondelete="CASCADE"),
        primary_key=True,
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game_questions.id", ondelete="CASCADE"),
        primary_key=True,
    )

    exp_awarded: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    awarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    user_gamification: Mapped["UserGamification"] = relationship(
        back_populates="question_exp",
    )


class LevelAttempt(Base):
    __tablename__ = "level_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "user_gamification.user_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "game_levels.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    hearts_lost: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    correct_answers: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    wrong_answers: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    exp_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_perfect: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    attempts: Mapped[list["UserQuestionAttempt"]] = relationship(
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_level_attempt_user_started",
            "user_id",
            "started_at",
        ),
    )