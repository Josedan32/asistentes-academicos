import type { DragEndEvent } from "@dnd-kit/core";

export function computeDragMove(
  event: DragEndEvent
): { courseId: number; newSemester: number } | null {
  const { active, over } = event;
  if (!over) return null;

  const match = String(over.id).match(/^semester-(\d+)$/);
  if (!match) return null;

  const courseId = Number(active.id);
  if (!Number.isFinite(courseId)) return null;

  return { courseId, newSemester: Number(match[1]) };
}
