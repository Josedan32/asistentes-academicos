export function describeToolCall(name: string, args: Record<string, unknown>): string {
  switch (name) {
    case "get_prerequisites":
      return `Consultando prerrequisitos de "${args.course}"`;
    case "list_semester_courses":
      return `Consultando materias del semestre ${args.semester}`;
    case "get_course_detail":
      return `Consultando detalle de "${args.course}"`;
    case "find_course_in_programs":
      return `Buscando "${args.course}" en otras carreras`;
    default:
      return `Ejecutando ${name}`;
  }
}
