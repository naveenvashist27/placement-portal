from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    Difficulty,
    EventStatus,
    ExperienceStatus,
    FormStatus,
    QuestionSubmissionStatus,
)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    question_links: Mapped[list["QuestionTopic"]] = relationship(back_populates="topic")


class InterviewQuestion(Base):
    """Canonical verified question shown to students."""

    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    company_year_id: Mapped[int | None] = mapped_column(ForeignKey("company_years.id"), nullable=True, index=True)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("company_roles.id"), nullable=True, index=True)
    round_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    question_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(String(512), index=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.UNKNOWN)
    frequency: Mapped[int] = mapped_column(Integer, default=1)
    is_public: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    submissions: Mapped[list["QuestionSubmission"]] = relationship(back_populates="canonical_question")
    topic_links: Mapped[list["QuestionTopic"]] = relationship(back_populates="question")


class QuestionSubmission(Base):
    __tablename__ = "question_submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    submitted_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(String(512), index=True)
    status: Mapped[QuestionSubmissionStatus] = mapped_column(
        Enum(QuestionSubmissionStatus), default=QuestionSubmissionStatus.PENDING, index=True
    )
    canonical_question_id: Mapped[int | None] = mapped_column(
        ForeignKey("interview_questions.id"), nullable=True, index=True
    )
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    company_year_id: Mapped[int | None] = mapped_column(ForeignKey("company_years.id"), nullable=True)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("company_roles.id"), nullable=True)
    round_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.UNKNOWN)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    canonical_question: Mapped[InterviewQuestion | None] = relationship(back_populates="submissions")


class QuestionTopic(Base):
    __tablename__ = "question_topics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("interview_questions.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)

    question: Mapped[InterviewQuestion] = relationship(back_populates="topic_links")
    topic: Mapped[Topic] = relationship(back_populates="question_links")


class InterviewExperience(Base):
    __tablename__ = "interview_experiences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    company_year_id: Mapped[int] = mapped_column(ForeignKey("company_years.id"), index=True)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("company_roles.id"), nullable=True)
    overall_experience: Mapped[str] = mapped_column(Text)
    preparation_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.UNKNOWN)
    selection_outcome: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[ExperienceStatus] = mapped_column(Enum(ExperienceStatus), default=ExperienceStatus.PENDING, index=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    rounds: Mapped[list["InterviewRound"]] = relationship(back_populates="experience", cascade="all, delete-orphan")


class InterviewRound(Base):
    __tablename__ = "interview_rounds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    experience_id: Mapped[int] = mapped_column(ForeignKey("interview_experiences.id", ondelete="CASCADE"), index=True)
    round_number: Mapped[int] = mapped_column(Integer)
    round_type: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.UNKNOWN)

    experience: Mapped[InterviewExperience] = relationship(back_populates="rounds")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    registration_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    event_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    registration_form_id: Mapped[int | None] = mapped_column(ForeignKey("registration_forms.id"), nullable=True)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.DRAFT, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RegistrationForm(Base):
    __tablename__ = "registration_forms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("company_roles.id"), nullable=True)
    registration_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    form_fields_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    eligibility_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[FormStatus] = mapped_column(Enum(FormStatus), default=FormStatus.DRAFT, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    registrations: Mapped[list["Registration"]] = relationship(back_populates="form", cascade="all, delete-orphan")


class Registration(Base):
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("registration_forms.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    responses_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    form: Mapped[RegistrationForm] = relationship(back_populates="registrations")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    notification_type: Mapped[str] = mapped_column(String(32), default="INFO")
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
