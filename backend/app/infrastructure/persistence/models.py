from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
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
