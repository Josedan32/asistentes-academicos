export function describeAssistants(
  programName: string, semester: number, courseNames: string[]
): string {
  const prefix = `Con ${programName} · semestre ${semester}`;

  if (courseNames.length === 0) {
    return (
      `${prefix} tendrás el asistente general de carrera. Aún no hay materias asignadas a ` +
      "ese semestre en la malla."
    );
  }

  const list =
    courseNames.length === 1
      ? courseNames[0]
      : `${courseNames.slice(0, -1).join(", ")} y ${courseNames[courseNames.length - 1]}`;

  return `${prefix} tendrás asistentes para ${list}, además del asistente general de carrera.`;
}
