from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import (
    get_academic_reader,
    get_academic_repository,
    require_coordination,
)
from app.api.v1.schemas import (
    CourseIn,
    CourseOut,
    CoursePlacementOut,
    CourseWithUsageOut,
    CurriculumAssignmentIn,
    CurriculumBoardEntryOut,
    CurriculumBoardPrerequisiteOut,
    CurriculumEntryOut,
    CurriculumMoveIn,
    ProgramIn,
    ProgramOut,
)
from app.application.academic.commands import (
    AssignCourseToCurriculum,
    CreateCourse,
    CreateProgram,
    MoveCourseToSemester,
)
from app.application.academic.queries import GetCurriculumBoard, ListCourses, ListPrograms
from app.domain.academic.exceptions import AcademicError
from app.infrastructure.persistence.academic_reader import SqlAlchemyAcademicReader
from app.infrastructure.persistence.academic_repository import SqlAlchemyAcademicRepository

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_coordination)],
)

RepoDep = Annotated[SqlAlchemyAcademicRepository, Depends(get_academic_repository)]
ReaderDep = Annotated[SqlAlchemyAcademicReader, Depends(get_academic_reader)]


@router.get("/programs", response_model=list[ProgramOut])
async def list_programs(reader: ReaderDep) -> list[ProgramOut]:
    rows = await ListPrograms(reader).execute()
    return [
        ProgramOut(
            id=row.id,
            code=row.code,
            name=row.name,
            semester_count=row.semester_count,
            is_active=row.is_active,
            course_count=row.course_count,
        )
        for row in rows
    ]


@router.post("/programs", status_code=status.HTTP_201_CREATED, response_model=ProgramOut)
async def create_program(payload: ProgramIn, repository: RepoDep) -> ProgramOut:
    try:
        program = await CreateProgram(repository).execute(
            code=payload.code,
            name=payload.name,
            semester_count=payload.semester_count,
            is_active=payload.is_active,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    assert program.id is not None
    return ProgramOut(
        id=program.id,
        code=program.code,
        name=program.name,
        semester_count=program.semester_count,
        is_active=program.is_active,
    )


@router.post("/courses", status_code=status.HTTP_201_CREATED, response_model=CourseOut)
async def create_course(payload: CourseIn, repository: RepoDep) -> CourseOut:
    try:
        course = await CreateCourse(repository).execute(
            code=payload.code,
            name=payload.name,
            area=payload.area,
            default_credits=payload.default_credits,
            description=payload.description,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    assert course.id is not None
    return CourseOut(
        id=course.id,
        code=course.code,
        name=course.name,
        area=course.area,
        default_credits=course.default_credits,
    )


@router.get("/courses", response_model=list[CourseWithUsageOut])
async def list_courses(reader: ReaderDep) -> list[CourseWithUsageOut]:
    rows = await ListCourses(reader).execute()
    return [
        CourseWithUsageOut(
            id=r.id, code=r.code, name=r.name, area=r.area,
            default_credits=r.default_credits,
            placements=[
                CoursePlacementOut(program_id=p.program_id, program_code=p.program_code,
                                     program_name=p.program_name, semester=p.semester,
                                     credits=p.credits)
                for p in r.placements
            ],
        )
        for r in rows
    ]


@router.post(
    "/programs/{program_id}/curriculum",
    status_code=status.HTTP_201_CREATED,
    response_model=CurriculumEntryOut,
)
async def assign_course(
    program_id: int, payload: CurriculumAssignmentIn, repository: RepoDep
) -> CurriculumEntryOut:
    try:
        entry = await AssignCourseToCurriculum(repository).execute(
            program_id=program_id,
            course_id=payload.course_id,
            semester=payload.semester,
            credits=payload.credits,
            prerequisite_course_ids=tuple(payload.prerequisite_course_ids),
        )
    except AcademicError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error

    return CurriculumEntryOut(
        course_id=entry.course_id,
        semester=entry.semester,
        credits=entry.credits,
        prerequisite_course_ids=list(entry.prerequisite_course_ids),
    )


@router.get(
    "/programs/{program_id}/curriculum",
    response_model=list[CurriculumBoardEntryOut],
)
async def get_curriculum_board(
    program_id: int, reader: ReaderDep
) -> list[CurriculumBoardEntryOut]:
    rows = await GetCurriculumBoard(reader).execute(program_id=program_id)
    return [
        CurriculumBoardEntryOut(
            course_id=r.course_id,
            course_code=r.course_code,
            course_name=r.course_name,
            semester=r.semester,
            credits=r.credits,
            prerequisites=[
                CurriculumBoardPrerequisiteOut(
                    course_id=p.course_id, course_code=p.course_code, course_name=p.course_name
                )
                for p in r.prerequisites
            ],
            shared_program_count=r.shared_program_count,
        )
        for r in rows
    ]


@router.patch(
    "/programs/{program_id}/curriculum/{course_id}", response_model=CurriculumEntryOut
)
async def move_course(
    program_id: int, course_id: int, payload: CurriculumMoveIn, repository: RepoDep
) -> CurriculumEntryOut:
    try:
        entry = await MoveCourseToSemester(repository).execute(
            program_id=program_id, course_id=course_id, new_semester=payload.new_semester
        )
    except AcademicError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error

    return CurriculumEntryOut(
        course_id=entry.course_id,
        semester=entry.semester,
        credits=entry.credits,
        prerequisite_course_ids=list(entry.prerequisite_course_ids),
    )
