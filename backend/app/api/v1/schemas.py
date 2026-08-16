from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class ProgramIn(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=160)
    semester_count: int = Field(ge=1, le=12)
    is_active: bool = True


class ProgramOut(BaseModel):
    id: int
    code: str
    name: str
    semester_count: int
    is_active: bool
    course_count: int = 0


class CourseIn(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=160)
    area: str = Field(default="", max_length=80)
    default_credits: int = Field(ge=1, le=12)
    description: str = ""


class CourseOut(BaseModel):
    id: int
    code: str
    name: str
    area: str
    default_credits: int


class CurriculumAssignmentIn(BaseModel):
    course_id: int
    semester: int = Field(ge=1, le=12)
    credits: int = Field(ge=1, le=12)
    prerequisite_course_ids: list[int] = Field(default_factory=list)


class CurriculumMoveIn(BaseModel):
    new_semester: int = Field(ge=1, le=12)


class CurriculumEntryOut(BaseModel):
    course_id: int
    semester: int
    credits: int
    prerequisite_course_ids: list[int]


class SemesterCourseOut(BaseModel):
    id: int
    code: str
    name: str
    area: str
    credits: int
    semester: int


class CurriculumBoardPrerequisiteOut(BaseModel):
    course_id: int
    course_code: str
    course_name: str


class CurriculumBoardEntryOut(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    semester: int
    credits: int
    prerequisites: list[CurriculumBoardPrerequisiteOut]
    shared_program_count: int


class CoursePlacementOut(BaseModel):
    program_id: int
    program_code: str
    program_name: str
    semester: int
    credits: int


class CourseWithUsageOut(BaseModel):
    id: int
    code: str
    name: str
    area: str
    default_credits: int
    placements: list[CoursePlacementOut]


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    document: str = Field(min_length=3, max_length=32)
    program_id: int
    current_semester: int = Field(ge=1, le=12)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class ChatIn(BaseModel):
    conversation_id: int | None = None
    course_id: int | None = None
    message: str = Field(min_length=1, max_length=2000)
    mode: str = "consulta"


class FeedbackIn(BaseModel):
    value: Literal["up", "down"]
    comment: str | None = Field(default=None, max_length=500)


class MeOut(BaseModel):
    id: int
    email: str
    role: str
    first_name: str | None = None
    last_name: str | None = None
    document: str | None = None
    program_id: int | None = None
    program_code: str | None = None
    program_name: str | None = None
    current_semester: int | None = None


class ModelOut(BaseModel):
    model: str


class ToolCallOut(BaseModel):
    id: int
    name: str
    arguments: dict[str, Any]
    result: Any
    duration_ms: int
    row_count: int
    sequence: int


class FeedbackOut(BaseModel):
    value: str
    comment: str | None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    mode: str | None
    tool_calls: list[ToolCallOut]
    feedback: FeedbackOut | None


class ConversationSummaryOut(BaseModel):
    id: int
    title: str
    course_id: int | None
    course_name: str | None
    created_at: datetime


class ConversationDetailOut(BaseModel):
    id: int
    title: str
    course_id: int | None
    course_name: str | None
    messages: list[MessageOut]


class CourseMaterialOut(BaseModel):
    id: int
    course_id: int
    filename: str


class ChatAttachmentOut(BaseModel):
    filename: str
    text: str


class EnrollmentOut(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    area: str
    credits: int
    period: str
    times_taken: int
