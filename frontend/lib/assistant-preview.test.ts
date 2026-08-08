import { describe, expect, it } from "vitest";
import { describeAssistants } from "./assistant-preview";

describe("describeAssistants", () => {
  it("lists every course plus the general assistant", () => {
    const text = describeAssistants("Ingeniería en Software", 5, [
      "Base de Datos 2", "Ingeniería de Software 1", "Sistemas Operativos", "Estadística",
    ]);
    expect(text).toBe(
      "Con Ingeniería en Software · semestre 5 tendrás asistentes para Base de Datos 2, " +
      "Ingeniería de Software 1, Sistemas Operativos y Estadística, además del asistente " +
      "general de carrera."
    );
  });

  it("handles a single course without an Oxford comma", () => {
    const text = describeAssistants("Ingeniería Mecánica", 2, ["Física Mecánica"]);
    expect(text).toBe(
      "Con Ingeniería Mecánica · semestre 2 tendrás asistentes para Física Mecánica, " +
      "además del asistente general de carrera."
    );
  });

  it("says so when no courses are assigned to that semester yet", () => {
    const text = describeAssistants("Tecnología en Producción Industrial", 6, []);
    expect(text).toBe(
      "Con Tecnología en Producción Industrial · semestre 6 tendrás el asistente general de " +
      "carrera. Aún no hay materias asignadas a ese semestre en la malla."
    );
  });
});
