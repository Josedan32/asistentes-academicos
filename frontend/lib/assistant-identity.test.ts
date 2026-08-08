import { describe, expect, it } from "vitest";
import { assistantInitials, assistantTitle } from "./assistant-identity";

describe("assistant-identity", () => {
  it("gives the general assistant GC initials and a fixed title", () => {
    const assistant = { type: "general" as const };
    expect(assistantInitials(assistant)).toBe("GC");
    expect(assistantTitle(assistant)).toBe("Asistente General de Carrera");
  });

  it("derives a per-course assistant's initials from its name", () => {
    const assistant = { type: "course" as const, courseId: 1, courseName: "Base de Datos 2" };
    expect(assistantInitials(assistant)).toBe("BD");
    expect(assistantTitle(assistant)).toBe("Asistente · Base de Datos 2");
  });

  it("handles a single-word course name", () => {
    const assistant = { type: "course" as const, courseId: 2, courseName: "Estadística" };
    expect(assistantInitials(assistant)).toBe("E");
  });
});
