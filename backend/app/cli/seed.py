"""Seed the database with a coordination account, a demo student, and the full
Ingenieria de Software curriculum (Institucion Universitaria Pascual Bravo, program
code 018, SNIES 107276).

Run: backend/.venv/Scripts/python.exe -m app.cli.seed
Coordination and student accounts are created here rather than through a UI — Phase 1
has no user-management screen by design. Safe to run more than once: rows that already
exist are skipped and reported, never re-created.

Required: SEED_COORDINATION_PASSWORD. Optional: SEED_STUDENT_PASSWORD — if unset, the
demo student is skipped (coordination and the curriculum still seed). Credentials are
never hardcoded here; see the root README's "Credenciales de prueba" section for the
values used in local development.
"""

import asyncio
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.academic.commands import (
    AssignCourseToCurriculum,
    CreateCourse,
    CreateProgram,
)
from app.application.academic.queries import ListPrograms
from app.application.identity.services import RegisterStudent
from app.domain.academic.exceptions import DuplicateCourseInCurriculumError
from app.domain.identity.entities import Role, User
from app.domain.identity.exceptions import EmailAlreadyRegisteredError
from app.infrastructure.persistence.academic_reader import SqlAlchemyAcademicReader
from app.infrastructure.persistence.academic_repository import SqlAlchemyAcademicRepository
from app.infrastructure.persistence.models import (
    AcademicHistoryRecordModel,
    StudentEnrollmentModel,
)
from app.infrastructure.persistence.session import create_session_factory
from app.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from app.infrastructure.security.hasher import Argon2Hasher

COORDINATION_EMAIL = "coordinacion@pascualbravo.edu.co"

STUDENT_EMAIL = "jose.hernandez540@pascualbravo.edu.co"
STUDENT_FIRST_NAME = "Jose"
STUDENT_LAST_NAME = "Hernandez"
STUDENT_DOCUMENT = "1000000001"
STUDENT_SEMESTER = 5

PROGRAM_CODE = "018"
PROGRAM_NAME = "Ingenieria de Software"

# (code, name, area, credits) — credits doubles as both Course.default_credits and this
# program's curriculum credits, since program 018 is the only program using any of these
# courses in this seed.
COURSES = [
    # Nivel 1
    ("ET0112", "Matematicas Discretas", "Fundamentacion basica", 2),
    ("ET0120", "Teoria General de Sistemas", "Formacion basica profesional", 2),
    ("ET0182", "Sistemas Operativos 1", "Formacion basica profesional", 2),
    ("ET0220", "Desarrollo de Pensamiento Computacional", "Fundamentacion especifica", 4),
    ("ET0221", "Taller de Desarrollo de Creatividad", "Formacion basica profesional", 4),
    ("FB0004", "Lengua Materna", "Formacion humanistica", 2),
    # Nivel 2
    ("ET0183", "Algoritmos", "Fundamentacion especifica", 2),
    ("ET0184", "Sistemas Operativos 2", "Formacion basica profesional", 4),
    ("ET0185", "Electronica Basica y Teoria de Circuitos Digitales",
     "Formacion basica profesional", 4),
    ("ET0186", "Habilidades de Comunicacion y Negociacion", "Formacion humanistica", 2),
    ("FB0001", "Matematicas Operativas", "Fundamentacion basica", 4),
    # Nivel 3
    ("ET0047", "Herramientas de Programacion I", "Formacion basica profesional", 4),
    ("ET0121", "Estructura de Datos", "Formacion basica profesional", 2),
    ("ET0187", "Bases de Datos 1", "Fundamentacion especifica", 3),
    ("FB0005", "Calculo Diferencial", "Fundamentacion basica", 4),
    ("FB0007", "Constitucion y Participacion Ciudadana", "Formacion humanistica", 2),
    ("FB0081", "Ingles 1", "Formacion humanistica", 1),
    # Nivel 4
    ("ET0051", "Herramientas de Programacion II", "Fundamentacion especifica", 4),
    ("ET0062", "Bases de Datos II", "Fundamentacion especifica", 4),
    ("ET0188", "Ingenieria de Software 1", "Fundamentacion especifica", 3),
    ("FB0008", "Calculo Integral", "Fundamentacion basica", 4),
    ("FB0082", "Ingles 2", "Formacion humanistica", 1),
    # Nivel 5
    ("ET0113", "Algebra Lineal", "Fundamentacion basica", 4),
    ("ET0189", "Metodos Numericos", "Fundamentacion basica", 2),
    ("ET0190", "Estadistica", "Fundamentacion basica", 2),
    ("ET0191", "Ingenieria de Software 2", "Fundamentacion especifica", 3),
    ("ET0192", "Redes y Comunicaciones de Datos", "Formacion basica profesional", 4),
    ("FB0083", "Ingles 3", "Formacion humanistica", 1),
    # Nivel 6
    ("ET0056", "Herramientas de Programacion III", "Fundamentacion especifica", 4),
    ("ET0193", "Matematicas Especiales", "Fundamentacion basica", 4),
    ("ET0194", "Inteligencia de Negocios (BI)", "Fundamentacion especifica", 3),
    ("ET0195", "Seguridad en Redes y Computacion en la Nube",
     "Formacion basica profesional", 4),
    ("FB0084", "Ingles 4", "Formacion humanistica", 1),
    # Nivel 7
    ("ET0196", "Investigacion de Operaciones", "Fundamentacion basica", 3),
    ("ET0197", "Programacion Avanzada", "Fundamentacion especifica", 4),
    ("ET0198", "Pruebas de Software", "Fundamentacion especifica", 4),
    ("FB0003", "Desarrollo Humano y Social", "Formacion humanistica", 2),
    ("FB0012", "Gestion Ambiental", "Formacion basica profesional", 2),
    ("FB0085", "Ingles 5", "Formacion humanistica", 1),
    # Nivel 8
    ("ET0018", "Metodologia de la Investigacion", "Formacion humanistica", 2),
    ("ET0199", "Modelos y Simulacion", "Fundamentacion basica", 4),
    ("ET0200", "Arquitectura de Software", "Fundamentacion especifica", 2),
    ("ET0201", "Electiva 1", "Formacion basica profesional", 4),
    ("ET0202", "Calidad de Software y Auditoria de Sistemas", "Fundamentacion especifica", 3),
    ("FB0086", "Ingles 6", "Formacion humanistica", 1),
    # Nivel 9
    ("ET0203", "Seminario de la Ciencia de los Datos", "Fundamentacion especifica", 4),
    ("ET0204", "Linea de Profundizacion 1", "Fundamentacion especifica", 4),
    ("ET0205", "Electiva 2", "Formacion basica profesional", 4),
    ("ET0206", "Gerencia de Proyectos de Sistemas", "Formacion basica profesional", 3),
    ("FB0087", "Ingles 7", "Formacion humanistica", 1),
    # Nivel 10
    ("ET0207", "Seminario de Emprendimiento e Innovacion", "Formacion basica profesional", 4),
    ("ET0208", "Linea de Profundizacion 2", "Fundamentacion especifica", 4),
    ("ET0209", "Seminario de Gestion y Gobierno de Tecnologia",
     "Formacion basica profesional", 3),
    ("ET0210", "Trabajo de Grado / Practica", "Fundamentacion especifica", 4),
    ("FB0088", "Ingles 8", "Formacion humanistica", 1),
]

# (code, semester, credits, prerequisite codes). Prerequisites are always assigned in an
# earlier semester, and this list is ordered by semester so every prerequisite is already
# in the curriculum by the time it is referenced — Curriculum.assign() requires that.
ASSIGNMENTS = [
    # Nivel 1
    ("ET0112", 1, 2, ()),
    ("ET0120", 1, 2, ()),
    ("ET0182", 1, 2, ()),
    ("ET0220", 1, 4, ()),
    ("ET0221", 1, 4, ()),
    ("FB0004", 1, 2, ()),
    # Nivel 2
    ("ET0183", 2, 2, ("ET0220",)),
    ("ET0184", 2, 4, ("ET0182",)),
    ("ET0185", 2, 4, ()),
    ("ET0186", 2, 2, ()),
    ("FB0001", 2, 4, ()),
    # Nivel 3
    ("ET0047", 3, 4, ("ET0183",)),
    ("ET0121", 3, 2, ("ET0183",)),
    ("ET0187", 3, 3, ()),
    ("FB0005", 3, 4, ("FB0001",)),
    ("FB0007", 3, 2, ()),
    ("FB0081", 3, 1, ()),
    # Nivel 4
    ("ET0051", 4, 4, ("ET0047",)),
    ("ET0062", 4, 4, ("ET0187",)),
    ("ET0188", 4, 3, ("ET0187",)),
    ("FB0008", 4, 4, ("FB0005",)),
    ("FB0082", 4, 1, ("FB0081",)),
    # Nivel 5
    ("ET0113", 5, 4, ()),
    ("ET0189", 5, 2, ("FB0008",)),
    ("ET0190", 5, 2, ()),
    ("ET0191", 5, 3, ("ET0051", "ET0188")),
    ("ET0192", 5, 4, ()),
    ("FB0083", 5, 1, ("FB0082",)),
    # Nivel 6
    ("ET0056", 6, 4, ("ET0051",)),
    ("ET0193", 6, 4, ("ET0113",)),
    ("ET0194", 6, 3, ("ET0190",)),
    ("ET0195", 6, 4, ("ET0192",)),
    ("FB0084", 6, 1, ("FB0083",)),
    # Nivel 7
    ("ET0196", 7, 3, ("ET0193",)),
    ("ET0197", 7, 4, ("ET0051",)),
    ("ET0198", 7, 4, ("ET0191", "ET0195")),
    ("FB0003", 7, 2, ()),
    ("FB0012", 7, 2, ()),
    ("FB0085", 7, 1, ("FB0084",)),
    # Nivel 8
    ("ET0018", 8, 2, ()),
    ("ET0199", 8, 4, ("ET0196",)),
    ("ET0200", 8, 2, ("ET0191", "ET0056")),
    ("ET0201", 8, 4, ("ET0051",)),
    ("ET0202", 8, 3, ("ET0198",)),
    ("FB0086", 8, 1, ("FB0085",)),
    # Nivel 9
    ("ET0203", 9, 4, ("ET0194",)),
    ("ET0204", 9, 4, ()),
    ("ET0205", 9, 4, ()),
    ("ET0206", 9, 3, ("ET0191", "ET0202")),
    ("FB0087", 9, 1, ("FB0086",)),
    # Nivel 10
    ("ET0207", 10, 4, ()),
    ("ET0208", 10, 4, ("ET0204",)),
    ("ET0209", 10, 3, ()),
    ("ET0210", 10, 4, ("ET0191", "ET0018", "ET0206")),
    ("FB0088", 10, 1, ("FB0087",)),
]

# (period, course_code, status, grade, concept, times_taken) — the demo student's real
# transcript, supplied directly by the project owner rather than parsed from an upload
# (no transcript-import UI exists yet).
ACADEMIC_HISTORY = [
    ("20242", "ET0112", "Aprobada", 3.3, None, 1),
    ("20242", "ET0120", "Aprobada", 4.0, None, 1),
    ("20242", "ET0182", "Aprobada", 4.5, None, 1),
    ("20242", "ET0220", "Aprobada", 4.1, None, 1),
    ("20242", "ET0221", "Aprobada", 4.1, None, 1),
    ("20242", "FB0004", "Aprobada", 4.8, None, 1),
    ("20251", "ET0183", "Aprobada", 4.7, None, 1),
    ("20251", "ET0184", "Aprobada", 4.3, None, 1),
    ("20251", "ET0185", "Aprobada", 3.8, None, 1),
    ("20251", "ET0186", "Aprobada", 4.8, None, 1),
    ("20251", "FB0001", "Aprobada", 4.2, None, 1),
    ("20252", "ET0047", "Aprobada", 4.0, None, 1),
    ("20252", "ET0121", "Aprobada", 4.9, None, 1),
    ("20252", "ET0187", "Aprobada", 4.0, None, 1),
    ("20252", "FB0005", "Aprobada", 3.6, None, 1),
    ("20252", "FB0007", "Aprobada", 3.2, None, 1),
    ("20261", "ET0051", "Aprobada", 5.0, None, 1),
    ("20261", "ET0062", "Aprobada", 4.4, None, 1),
    ("20261", "ET0188", "Aprobada", 4.6, None, 1),
    ("20261", "FB0008", "Aprobada", 4.1, None, 1),
    ("20261", "FB0081", "Aprobada", 4.0, "Examen especial", 1),
    ("20261", "FB0082", "Aprobada", 4.0, "Examen especial", 1),
    ("20261", "FB0083", "Aprobada", 4.0, "Examen especial", 1),
    ("20261", "FB0084", "Aprobada", 4.0, "Examen especial", 1),
    ("20261", "FB0085", "Aprobada", 4.0, "Examen especial", 1),
    ("20261", "FB0086", "Aprobada", 4.8, None, 1),
]

# (period, course_code, times_taken) — courses the student is actually registered in this
# period. Independent of what the static curriculum lists for their current_semester: a
# real student's pace (repeats, cancellations, testing out of levels early) can diverge
# from that grouping, as it does here — Ingles 7 is nominally a semester-9 course.
CURRENT_ENROLLMENTS = [
    ("20262", "ET0113", 0),
    ("20262", "ET0189", 0),
    ("20262", "ET0190", 0),
    ("20262", "ET0191", 0),
    ("20262", "ET0192", 0),
    ("20262", "FB0087", 0),
]


async def main() -> None:
    coordination_password = os.environ.get("SEED_COORDINATION_PASSWORD")
    if not coordination_password:
        raise SystemExit(
            "Set SEED_COORDINATION_PASSWORD before seeding. "
            "Do not hardcode credentials."
        )
    student_password = os.environ.get("SEED_STUDENT_PASSWORD")

    factory = create_session_factory()
    async with factory() as session:
        users = SqlAlchemyUserRepository(session)
        hasher = Argon2Hasher()

        if await users.find_by_email(COORDINATION_EMAIL) is None:
            await users.add(
                User(
                    email=COORDINATION_EMAIL,
                    password_hash=hasher.hash(coordination_password),
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

        if student_password is None:
            print("skipped demo student (SEED_STUDENT_PASSWORD not set)")
        else:
            try:
                await RegisterStudent(users, hasher).execute(
                    email=STUDENT_EMAIL,
                    password=student_password,
                    first_name=STUDENT_FIRST_NAME,
                    last_name=STUDENT_LAST_NAME,
                    document=STUDENT_DOCUMENT,
                    program_id=program_id,
                    current_semester=STUDENT_SEMESTER,
                )
                print(f"created student account {STUDENT_EMAIL}")
            except EmailAlreadyRegisteredError:
                print(f"skipped student account {STUDENT_EMAIL} (already exists)")

        student = await users.find_by_email(STUDENT_EMAIL)
        if student is None:
            print(f"skipped academic history (student account {STUDENT_EMAIL} does not exist)")
        else:
            assert student.id is not None
            await _seed_academic_history(session, student.id, created)
            await _seed_current_enrollments(session, student.id, created)


async def _seed_academic_history(
    session: AsyncSession, student_user_id: int, course_ids: dict[str, int]
) -> None:
    existing = {
        (row.course_id, row.period)
        for row in (
            await session.execute(
                select(AcademicHistoryRecordModel).where(
                    AcademicHistoryRecordModel.student_user_id == student_user_id
                )
            )
        ).scalars()
    }
    added = 0
    for period, code, status, grade, concept, times_taken in ACADEMIC_HISTORY:
        course_id = course_ids.get(code)
        if course_id is None or (course_id, period) in existing:
            continue
        session.add(
            AcademicHistoryRecordModel(
                student_user_id=student_user_id, course_id=course_id, period=period,
                status=status, grade=grade, concept=concept, times_taken=times_taken,
            )
        )
        added += 1
    await session.commit()
    print(f"seeded {added} academic history rows for {STUDENT_EMAIL}")


async def _seed_current_enrollments(
    session: AsyncSession, student_user_id: int, course_ids: dict[str, int]
) -> None:
    existing = {
        (row.course_id, row.period)
        for row in (
            await session.execute(
                select(StudentEnrollmentModel).where(
                    StudentEnrollmentModel.student_user_id == student_user_id
                )
            )
        ).scalars()
    }
    added = 0
    for period, code, times_taken in CURRENT_ENROLLMENTS:
        course_id = course_ids.get(code)
        if course_id is None or (course_id, period) in existing:
            continue
        session.add(
            StudentEnrollmentModel(
                student_user_id=student_user_id, course_id=course_id, period=period,
                times_taken=times_taken,
            )
        )
        added += 1
    await session.commit()
    print(f"seeded {added} enrollment rows for {STUDENT_EMAIL}")


if __name__ == "__main__":
    asyncio.run(main())
