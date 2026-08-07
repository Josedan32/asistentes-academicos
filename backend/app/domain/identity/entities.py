from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    COORDINATION = "coordination"
    STUDENT = "student"


@dataclass(frozen=True)
class User:
    email: str
    password_hash: str
    role: Role
    id: int | None = None

    def __post_init__(self) -> None:
        if "@" not in self.email:
            raise ValueError("email must contain '@'")


@dataclass(frozen=True)
class StudentProfile:
    user_id: int
    first_name: str
    last_name: str
    document: str
    program_id: int
    current_semester: int
