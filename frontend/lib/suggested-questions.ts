import type { ActiveAssistant } from "./assistant-identity";

const GENERAL_SUGGESTIONS = [
  "¿Qué prerrequisitos me faltan para ver Base de Datos 2?",
  "¿Qué materias puedo matricular en semestre 6?",
  "¿Qué materias comparte mi carrera con Ing. Electrónica?",
  "¿Cuáles son los prerrequisitos de Sistemas Operativos?",
];

export function suggestedQuestionsFor(assistant: ActiveAssistant): string[] {
  if (assistant.type === "general") return GENERAL_SUGGESTIONS;

  const course = assistant.courseName;
  return [
    `¿Cuáles son los prerrequisitos de ${course}?`,
    `¿Cuántos créditos tiene ${course} en mi carrera?`,
    `¿En qué otras carreras se ve ${course}?`,
    `Cuéntame los detalles de ${course}.`,
  ];
}
