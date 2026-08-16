from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ProgramModel(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    semester_count: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CourseModel(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    normalized_name: Mapped[str] = mapped_column(String(160), index=True, default="")
    area: Mapped[str] = mapped_column(String(80), default="")
    default_credits: Mapped[int] = mapped_column(Integer, default=3)
    description: Mapped[str] = mapped_column(Text, default="")


class CurriculumEntryModel(Base):
    __tablename__ = "curriculum_entries"
    __table_args__ = (UniqueConstraint("program_id", "course_id", name="uq_program_course"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    semester: Mapped[int] = mapped_column(Integer, index=True)
    credits: Mapped[int] = mapped_column(Integer)


class PrerequisiteModel(Base):
    __tablename__ = "prerequisites"
    __table_args__ = (
        UniqueConstraint("curriculum_entry_id", "required_course_id", name="uq_entry_required"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    curriculum_entry_id: Mapped[int] = mapped_column(
        ForeignKey("curriculum_entries.id", ondelete="CASCADE")
    )
    required_course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class StudentProfileModel(Base):
    __tablename__ = "student_profiles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    document: Mapped[str] = mapped_column(String(32))
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id", ondelete="RESTRICT"))
    current_semester: Mapped[int] = mapped_column(Integer)


class AcademicHistoryRecordModel(Base):
    __tablename__ = "academic_history_records"
    __table_args__ = (
        UniqueConstraint(
            "student_user_id", "course_id", "period", name="uq_history_student_course_period"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_user_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.user_id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    period: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20))
    grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    concept: Mapped[str | None] = mapped_column(String(40), nullable=True)
    times_taken: Mapped[int] = mapped_column(Integer, default=1)


class StudentEnrollmentModel(Base):
    __tablename__ = "student_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "student_user_id", "course_id", "period", name="uq_enrollment_student_course_period"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_user_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.user_id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"))
    period: Mapped[str] = mapped_column(String(10))
    times_taken: Mapped[int] = mapped_column(Integer, default=0)


class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    course_id: Mapped[int | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ToolCallModel(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80))
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON)
    result: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer)
    row_count: Mapped[int] = mapped_column(Integer)
    sequence: Mapped[int] = mapped_column(Integer)


class MessageFeedbackModel(Base):
    __tablename__ = "message_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True
    )
    value: Mapped[str] = mapped_column(String(4))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CourseMaterialModel(Base):
    __tablename__ = "course_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class MaterialChunkModel(Base):
    __tablename__ = "material_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(
        ForeignKey("course_materials.id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(JSON)
