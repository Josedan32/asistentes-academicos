import { describe, expect, it } from "vitest";
import { suggestedQuestionsFor } from "./suggested-questions";

describe("suggestedQuestionsFor", () => {
  it("returns the general four questions for the general assistant", () => {
    const questions = suggestedQuestionsFor({ type: "general" });
    expect(questions).toHaveLength(4);
    expect(questions.every((q) => !q.includes("undefined"))).toBe(true);
  });

  it("returns course-specific questions naming the active course", () => {
    const questions = suggestedQuestionsFor({
      type: "course", courseId: 1, courseName: "Base de Datos 2",
    });
    expect(questions).toHaveLength(4);
    expect(questions.every((q) => q.includes("Base de Datos 2"))).toBe(true);
  });

  it("changes when the active course changes", () => {
    const bd2 = suggestedQuestionsFor({ type: "course", courseId: 1, courseName: "Base de Datos 2" });
    const calc = suggestedQuestionsFor({ type: "course", courseId: 2, courseName: "Cálculo Diferencial" });
    expect(bd2).not.toEqual(calc);
  });
});
