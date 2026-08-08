import { describe, expect, it } from "vitest";
import { groupBoardBySemester } from "./group-board-by-semester";
import type { CurriculumBoardEntryOut } from "./types";

function entry(overrides: Partial<CurriculumBoardEntryOut>): CurriculumBoardEntryOut {
  return {
    course_id: 1, course_code: "X", course_name: "X", semester: 1, credits: 3,
    prerequisites: [], shared_program_count: 1, ...overrides,
  };
}

describe("groupBoardBySemester", () => {
  it("groups entries under their semester and leaves empty semesters as empty arrays", () => {
    const board = [entry({ course_id: 1, semester: 1 }), entry({ course_id: 2, semester: 3 })];

    const grouped = groupBoardBySemester(board, 4);

    expect(grouped.get(1)?.map((e) => e.course_id)).toEqual([1]);
    expect(grouped.get(2)).toEqual([]);
    expect(grouped.get(3)?.map((e) => e.course_id)).toEqual([2]);
    expect(grouped.get(4)).toEqual([]);
  });

  it("returns exactly semesterCount keys, 1-indexed", () => {
    const grouped = groupBoardBySemester([], 3);
    expect([...grouped.keys()]).toEqual([1, 2, 3]);
  });
});
