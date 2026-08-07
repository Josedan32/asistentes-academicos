"""Seed the database with a coordination account and the pilot curriculum.

Run: backend/.venv/Scripts/python.exe -m app.cli.seed
Coordination accounts are created here rather than through a UI — Phase 1 has no
user-management screen by design. Safe to run more than once: rows that already
exist are skipped and reported, never re-created.
"""

import asyncio
import os

from app.application.academic.commands import (
    AssignCourseToCurriculum,
    CreateCourse,
    CreateProgram,
)
from app.application.academic.queries import ListPrograms
from app.domain.academic.exceptions import DuplicateCourseInCurriculumError
from app.domain.identity.entities import Role, User
from app.infrastructure.persistence.academic_reader import SqlAlchemyAcademicReader
from app.infrastructure.persistence.academic_repository import SqlAlchemyAcademicRepository
from app.infrastructure.persistence.session import create_session_factory
from app.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from app.infrastructure.security.hasher import Argon2Hasher

COORDINATION_EMAIL = "coordinacion@pascualbravo.edu.co"
PROGRAM_CODE = "ISW"
PROGRAM_NAME = "Ingenieria en Software"

COURSES = [
    ("BD1", "Base de Datos 1", "Datos", 3),
    ("BD2", "Base de Datos 2", "Datos", 4),
    ("HP1", "Herramientas de Programacion 1", "Programacion", 3),
    ("HP2", "Herramientas de Programacion 2", "Programacion", 3),
    ("IS1", "Ingenieria de Software 1", "Ingenieria", 3),
]

ASSIGNMENTS = [
    ("BD1", 3, 3, ()),
    ("HP1", 3, 3, ()),
    ("BD2", 4, 4, ("BD1",)),
    ("HP2", 4, 3, ("HP1",)),
    ("IS1", 4, 3, ()),
]


async def main() -> None:
    password = os.environ.get("SEED_COORDINATION_PASSWORD")
    if not password:
        raise SystemExit(
            "Set SEED_COORDINATION_PASSWORD before seeding. "
            "Do not hardcode credentials."
        )

    factory = create_session_factory()
    async with factory() as session:
        users = SqlAlchemyUserRepository(session)
        if await users.find_by_email(COORDINATION_EMAIL) is None:
            hasher = Argon2Hasher()
            await users.add(
                User(
                    email=COORDINATION_EMAIL,
                    password_hash=hasher.hash(password),
                    role=Role.COORDINATION,
                ),
                None,
            )
            print(f"created coordination account {COORDINATION_EMAIL}")
        else:
            print(f"skipped coordination account {COORDINATION_EMAIL} (already exists)")

        reader = SqlAlchemyAcademicReader(session)
        repository = SqlAlchemyAcademicRepository(session)

        existing_programs = {p.code: p.id for p in await ListPrograms(reader).execute()}
        if PROGRAM_CODE in existing_programs:
            program_id = existing_programs[PROGRAM_CODE]
            print(f"skipped program {PROGRAM_CODE} (already exists)")
        else:
            program = await CreateProgram(repository).execute(
                code=PROGRAM_CODE, name=PROGRAM_NAME, semester_count=10
            )
            assert program.id is not None
            program_id = program.id
            print(f"created program {PROGRAM_CODE}")

        existing_courses = {c.code: c.id for c in await reader.course_candidates()}
        created: dict[str, int] = {}
        for code, name, area, credits in COURSES:
            if code in existing_courses:
                created[code] = existing_courses[code]
                print(f"skipped course {code} (already exists)")
                continue
            course = await CreateCourse(repository).execute(
                code=code, name=name, area=area, default_credits=credits
            )
            assert course.id is not None
            created[code] = course.id
            print(f"created course {code}")

        assign = AssignCourseToCurriculum(repository)
        for code, semester, credits, prerequisites in ASSIGNMENTS:
            try:
                await assign.execute(
                    program_id=program_id,
                    course_id=created[code],
                    semester=semester,
                    credits=credits,
                    prerequisite_course_ids=tuple(created[p] for p in prerequisites),
                )
                print(f"assigned {code} to semester {semester}")
            except DuplicateCourseInCurriculumError:
                print(f"skipped curriculum entry for {code} (already assigned)")

        print(f"seeded program {PROGRAM_CODE} with {len(COURSES)} courses")


if __name__ == "__main__":
    asyncio.run(main())
