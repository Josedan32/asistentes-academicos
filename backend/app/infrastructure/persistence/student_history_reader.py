from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.academic.dto import AcademicHistoryEntry, EnrollmentEntry
from app.infrastructure.persistence.models import (
    AcademicHistoryRecordModel,
    CourseModel,
    StudentEnrollmentModel,
)


class SqlAlchemyStudentHistoryReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def history_of(self, student_user_id: int) -> list[AcademicHistoryEntry]:
        rows = (
            await self._session.execute(
                select(AcademicHistoryRecordModel, CourseModel)
                .join(CourseModel, CourseModel.id == AcademicHistoryRecordModel.course_id)
                .where(AcademicHistoryRecordModel.student_user_id == student_user_id)
                .order_by(AcademicHistoryRecordModel.period, CourseModel.name)
            )
        ).all()
        return [
            AcademicHistoryEntry(
                course_id=course.id, course_code=course.code, course_name=course.name,
                area=course.area, credits=course.default_credits, period=record.period,
                status=record.status, grade=record.grade, concept=record.concept,
                times_taken=record.times_taken,
            )
            for record, course in rows
        ]

    async def enrollments_of(self, student_user_id: int) -> list[EnrollmentEntry]:
        rows = (
            await self._session.execute(
                select(StudentEnrollmentModel, CourseModel)
                .join(CourseModel, CourseModel.id == StudentEnrollmentModel.course_id)
                .where(StudentEnrollmentModel.student_user_id == student_user_id)
                .order_by(CourseModel.name)
            )
        ).all()
        return [
            EnrollmentEntry(
                course_id=course.id, course_code=course.code, course_name=course.name,
                area=course.area, credits=course.default_credits, period=enrollment.period,
                times_taken=enrollment.times_taken,
            )
            for enrollment, course in rows
        ]
