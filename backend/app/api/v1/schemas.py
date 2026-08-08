from typing import Literal

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
