import type { CourseWithUsageOut } from "./types";

export type CourseMatchStatus =
  | { status: "in-program"; semester: number }
  | { status: "shared"; otherProgramName: string; otherSemester: number }
  | { status: "unassigned" };

export function classifyCourseMatch(
  course: CourseWithUsageOut, programId: number
): CourseMatchStatus {
  const inProgram = course.placements.find((placement) => placement.program_id === programId);
  if (inProgram) return { status: "in-program", semester: inProgram.semester };

  const elsewhere = course.placements[0];
  if (elsewhere) {
    return {
      status: "shared", otherProgramName: elsewhere.program_name,
      otherSemester: elsewhere.semester,
    };
  }
  return { status: "unassigned" };
}
