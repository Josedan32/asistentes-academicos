"use client";

import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import type { CurriculumBoardEntryOut } from "@/lib/types";
import { CourseCard } from "./CourseCard";

export function DraggableCourseCard({ entry }: { entry: CurriculumBoardEntryOut }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: entry.course_id,
  });

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      style={{ transform: CSS.Translate.toString(transform), opacity: isDragging ? 0.4 : 1 }}
      className="cursor-grab"
    >
      <CourseCard entry={entry} />
    </div>
  );
}
