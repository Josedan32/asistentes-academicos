from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_academic_reader
from app.api.v1.schemas import ProgramOut, SemesterCourseOut
from app.application.academic.queries import ListPrograms, ListSemesterCourses
from app.infrastructure.persistence.academic_reader import SqlAlchemyAcademicReader

router = APIRouter(prefix="/api/v1", tags=["public"])

ReaderDep = Annotated[SqlAlchemyAcademicReader, Depends(get_academic_reader)]


@router.get("/programs", response_model=list[ProgramOut])
async def list_programs(reader: ReaderDep) -> list[ProgramOut]:
    rows = await ListPrograms(reader).execute()
    return [ProgramOut(**row.__dict__) for row in rows]


@router.get("/programs/{program_id}/curriculum", response_model=list[SemesterCourseOut])
async def list_curriculum(
    program_id: int,
    reader: ReaderDep,
    semester: Annotated[int, Query(ge=1, le=12)],
) -> list[SemesterCourseOut]:
    rows = await ListSemesterCourses(reader).execute(program_id=program_id, semester=semester)
    return [SemesterCourseOut(**row.__dict__) for row in rows]
