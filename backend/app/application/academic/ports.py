from typing import Protocol

from app.domain.academic.curriculum import Curriculum
from app.domain.academic.entities import Course, Program


class AcademicRepository(Protocol):
    """Write-side port. Loads and stores aggregates."""

    async def add_program(self, program: Program) -> Program: ...

    async def add_course(self, course: Course) -> Course: ...

    async def load_curriculum(self, program_id: int) -> Curriculum: ...

    async def save_curriculum(self, curriculum: Curriculum) -> None: ...

    async def course_exists(self, course_id: int) -> bool: ...
