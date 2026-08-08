import type { CurriculumBoardEntryOut } from "./types";

export function groupBoardBySemester(
  entries: CurriculumBoardEntryOut[], semesterCount: number
): Map<number, CurriculumBoardEntryOut[]> {
  const grouped = new Map<number, CurriculumBoardEntryOut[]>();
  for (let semester = 1; semester <= semesterCount; semester += 1) {
    grouped.set(semester, []);
  }
  for (const entry of entries) {
    grouped.get(entry.semester)?.push(entry);
  }
  return grouped;
}
