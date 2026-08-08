import { apiFetch } from "./client";
import type { ProgramOut, SemesterCourseOut } from "../types";

export function listPrograms(): Promise<ProgramOut[]> {
  return apiFetch<ProgramOut[]>("/api/v1/programs");
}

export function listCurriculum(
  programId: number, semester: number
): Promise<SemesterCourseOut[]> {
  return apiFetch<SemesterCourseOut[]>(
    `/api/v1/programs/${programId}/curriculum?semester=${semester}`
  );
}
