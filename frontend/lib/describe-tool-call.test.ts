import { describe, expect, it } from "vitest";
import { describeToolCall } from "./describe-tool-call";

describe("describeToolCall", () => {
  it("describes get_prerequisites", () => {
    expect(describeToolCall("get_prerequisites", { course: "Base de Datos 2" })).toBe(
      'Consultando prerrequisitos de "Base de Datos 2"'
    );
  });

  it("describes list_semester_courses", () => {
    expect(describeToolCall("list_semester_courses", { semester: 6 })).toBe(
      "Consultando materias del semestre 6"
    );
  });

  it("describes get_course_detail", () => {
    expect(describeToolCall("get_course_detail", { course: "Redes" })).toBe(
      'Consultando detalle de "Redes"'
    );
  });

  it("describes find_course_in_programs", () => {
    expect(describeToolCall("find_course_in_programs", { course: "Estadística" })).toBe(
      'Buscando "Estadística" en otras carreras'
    );
  });

  it("falls back to the raw tool name for anything unrecognized", () => {
    expect(describeToolCall("some_future_tool", {})).toBe("Ejecutando some_future_tool");
  });
});
