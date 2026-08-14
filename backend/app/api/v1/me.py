from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import (
    AcademicReaderDep,
    CurrentUser,
    StudentHistoryReaderDep,
    UserRepositoryDep,
    require_authentication,
    require_student,
)
from app.api.v1.schemas import EnrollmentOut, MeOut
from app.application.academic.queries import GetProgram
from app.domain.identity.entities import Role

router = APIRouter(prefix="/api/v1", tags=["me"])


@router.get("/me", response_model=MeOut)
async def get_me(
    user: Annotated[CurrentUser, Depends(require_authentication)],
    users: UserRepositoryDep,
    reader: AcademicReaderDep,
) -> MeOut:
    account = await users.find_by_id(user.user_id)
    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    if account.role != Role.STUDENT:
        return MeOut(id=user.user_id, email=account.email, role=str(account.role))

    profile = await users.find_profile_by_user_id(user.user_id)
    assert profile is not None, "a student account must have a profile"
    program = await GetProgram(reader).execute(program_id=profile.program_id)
    assert program is not None, "a student's program_id must reference a real program"

    return MeOut(
        id=user.user_id, email=account.email, role=str(account.role),
        first_name=profile.first_name, last_name=profile.last_name,
        document=profile.document, program_id=program.id, program_code=program.code,
        program_name=program.name, current_semester=profile.current_semester,
    )


@router.get("/me/enrollments", response_model=list[EnrollmentOut])
async def get_my_enrollments(
    user: Annotated[CurrentUser, Depends(require_student)],
    history_reader: StudentHistoryReaderDep,
) -> list[EnrollmentOut]:
    entries = await history_reader.enrollments_of(user.user_id)
    return [
        EnrollmentOut(
            course_id=e.course_id, course_code=e.course_code, course_name=e.course_name,
            area=e.area, credits=e.credits, period=e.period, times_taken=e.times_taken,
        )
        for e in entries
    ]
