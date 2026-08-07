from dataclasses import dataclass

from app.application.academic.ports import AcademicRepository
from app.domain.academic.entities import Course, CurriculumEntry, Program


@dataclass
class CreateProgram:
    repository: AcademicRepository

    async def execute(
        self, *, code: str, name: str, semester_count: int, is_active: bool = True
    ) -> Program:
        program = Program(
            code=code.strip().upper(),
            name=name.strip(),
            semester_count=semester_count,
            is_active=is_active,
        )
        return await self.repository.add_program(program)


@dataclass
class CreateCourse:
    repository: AcademicRepository

    async def execute(
        self,
        *,
        code: str,
        name: str,
        area: str,
        default_credits: int,
        description: str = "",
    ) -> Course:
        course = Course(
            code=code.strip().upper(),
            name=name.strip(),
            area=area.strip(),
            default_credits=default_credits,
            description=description.strip(),
        )
        return await self.repository.add_course(course)


@dataclass
class AssignCourseToCurriculum:
    repository: AcademicRepository

    async def execute(
        self,
        *,
        program_id: int,
        course_id: int,
        semester: int,
        credits: int,
        prerequisite_course_ids: tuple[int, ...] = (),
    ) -> CurriculumEntry:
        if not await self.repository.course_exists(course_id):
            raise LookupError(f"course {course_id} does not exist")

        curriculum = await self.repository.load_curriculum(program_id)
        entry = curriculum.assign(
            course_id=course_id,
            semester=semester,
            credits=credits,
            prerequisite_course_ids=prerequisite_course_ids,
        )
        await self.repository.save_curriculum(curriculum)
        return entry


@dataclass
class MoveCourseToSemester:
    repository: AcademicRepository

    async def execute(
        self, *, program_id: int, course_id: int, new_semester: int
    ) -> CurriculumEntry:
        curriculum = await self.repository.load_curriculum(program_id)
        entry = curriculum.move(course_id=course_id, new_semester=new_semester)
        await self.repository.save_curriculum(curriculum)
        return entry
