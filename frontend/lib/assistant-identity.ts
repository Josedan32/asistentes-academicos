export type ActiveAssistant =
  | { type: "general" }
  | { type: "course"; courseId: number; courseName: string };

export function assistantInitials(assistant: ActiveAssistant): string {
  if (assistant.type === "general") return "GC";
  const words = assistant.courseName.split(" ").filter(Boolean);
  const first = words[0]?.[0] ?? "";
  const second = words[1]?.[0] ?? "";
  return (first + second).toUpperCase();
}

export function assistantTitle(assistant: ActiveAssistant): string {
  return assistant.type === "general"
    ? "Asistente General de Carrera"
    : `Asistente · ${assistant.courseName}`;
}
