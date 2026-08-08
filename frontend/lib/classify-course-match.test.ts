import { describe, expect, it } from "vitest";
import { classifyCourseMatch } from "./classify-course-match";
import type { CourseWithUsageOut } from "./types";

function course(placements: CourseWithUsageOut["placements"]): CourseWithUsageOut {
  return { id: 1, code: "BDD-302", name: "Base de Datos 2", area: "Datos", default_credits: 3, placements };
}

describe("classifyCourseMatch", () => {
  it("reports in-program with its own semester when already in the target program", () => {
    const result = classifyCourseMatch(
      course([{ program_id: 1, program_code: "ISW", program_name: "Ing. Software", semester: 4, credits: 3 }]),
      1
    );
    expect(result).toEqual({ status: "in-program", semester: 4 });
  });

  it("reports shared with the other program's name and semester when used elsewhere only", () => {
    const result = classifyCourseMatch(
      course([{ program_id: 2, program_code: "IEL", program_name: "Ing. Electrónica", semester: 5, credits: 3 }]),
      1
    );
    expect(result).toEqual({ status: "shared", otherProgramName: "Ing. Electrónica", otherSemester: 5 });
  });

  it("reports unassigned when the course has no placements anywhere", () => {
    expect(classifyCourseMatch(course([]), 1)).toEqual({ status: "unassigned" });
  });

  it("prefers in-program over shared when the course is in both", () => {
    const result = classifyCourseMatch(
      course([
        { program_id: 1, program_code: "ISW", program_name: "Ing. Software", semester: 4, credits: 3 },
        { program_id: 2, program_code: "IEL", program_name: "Ing. Electrónica", semester: 5, credits: 3 },
      ]),
      1
    );
    expect(result.status).toBe("in-program");
  });
});
