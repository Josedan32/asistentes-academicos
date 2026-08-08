import { apiFetch } from "./client";
import type { CurriculumBoardEntryOut } from "../types";

export function getCurriculumBoard(programId: number): Promise<CurriculumBoardEntryOut[]> {
  return apiFetch<CurriculumBoardEntryOut[]>(`/api/v1/admin/programs/${programId}/curriculum`);
}

export function moveCourseToSemester(
  programId: number, courseId: number, newSemester: number
): Promise<unknown> {
  return apiFetch(`/api/v1/admin/programs/${programId}/curriculum/${courseId}`, {
    method: "PATCH", body: JSON.stringify({ new_semester: newSemester }),
  });
}

export interface AssignCoursePayload {
  course_id: number;
  semester: number;
  credits: number;
  prerequisite_course_ids: number[];
}

export function assignCourseToCurriculum(
  programId: number, payload: AssignCoursePayload
): Promise<unknown> {
  return apiFetch(`/api/v1/admin/programs/${programId}/curriculum`, {
    method: "POST", body: JSON.stringify(payload),
  });
}
