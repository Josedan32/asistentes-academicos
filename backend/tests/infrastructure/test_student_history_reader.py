from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models import (
    AcademicHistoryRecordModel,
    CourseModel,
    ProgramModel,
    StudentEnrollmentModel,
    StudentProfileModel,
    UserModel,
)
from app.infrastructure.persistence.student_history_reader import SqlAlchemyStudentHistoryReader


async def _student(session: AsyncSession, email: str = "ana@pascualbravo.edu.co") -> int:
    program = ProgramModel(code=f"p{abs(hash(email)) % 10000}", name="Ingenieria de Software",
                            semester_count=10)
    session.add(program)
    await session.flush()
    user = UserModel(email=email, password_hash="x", role="student")
    session.add(user)
    await session.flush()
    session.add(
        StudentProfileModel(
            user_id=user.id, first_name="Ana", last_name="Marin", document="1",
            program_id=program.id, current_semester=5,
        )
    )
    await session.commit()
    return user.id


async def test_history_of_returns_past_periods_ordered_and_joined_with_course(
    session: AsyncSession,
) -> None:
    student_id = await _student(session)
    course = CourseModel(code="ET0112", name="Matematicas Discretas", area="Fundamentacion",
                          default_credits=2)
    other_course = CourseModel(code="ET0120", name="Teoria General de Sistemas",
                                area="Formacion basica", default_credits=2)
    session.add_all([course, other_course])
    await session.flush()
    session.add_all([
        AcademicHistoryRecordModel(student_user_id=student_id, course_id=other_course.id,
                                    period="20242", status="Aprobada", grade=4.0,
                                    concept=None, times_taken=1),
        AcademicHistoryRecordModel(student_user_id=student_id, course_id=course.id,
                                    period="20242", status="Aprobada", grade=3.3,
                                    concept=None, times_taken=1),
    ])
    await session.commit()

    reader = SqlAlchemyStudentHistoryReader(session)
    entries = await reader.history_of(student_id)

    assert [e.course_name for e in entries] == [
        "Matematicas Discretas", "Teoria General de Sistemas",
    ]
    assert entries[0].grade == 3.3
    assert entries[0].status == "Aprobada"


async def test_history_of_only_returns_the_given_students_rows(session: AsyncSession) -> None:
    student_id = await _student(session)
    other_student_id = await _student(session, email="carlos@pascualbravo.edu.co")
    course = CourseModel(code="ET0112", name="Matematicas Discretas", area="Fundamentacion",
                          default_credits=2)
    session.add(course)
    await session.flush()
    session.add(
        AcademicHistoryRecordModel(student_user_id=other_student_id, course_id=course.id,
                                    period="20242", status="Aprobada", grade=4.0,
                                    concept=None, times_taken=1)
    )
    await session.commit()

    reader = SqlAlchemyStudentHistoryReader(session)
    assert await reader.history_of(student_id) == []


async def test_enrollments_of_returns_current_period_courses(session: AsyncSession) -> None:
    student_id = await _student(session)
    course = CourseModel(code="ET0113", name="Algebra Lineal", area="Fundamentacion basica",
                          default_credits=4)
    session.add(course)
    await session.flush()
    session.add(
        StudentEnrollmentModel(student_user_id=student_id, course_id=course.id,
                                period="20262", times_taken=0)
    )
    await session.commit()

    reader = SqlAlchemyStudentHistoryReader(session)
    entries = await reader.enrollments_of(student_id)

    assert len(entries) == 1
    assert entries[0].course_name == "Algebra Lineal"
    assert entries[0].period == "20262"
