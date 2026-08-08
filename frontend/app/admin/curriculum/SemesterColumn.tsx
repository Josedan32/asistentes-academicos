"use client";

import { useDroppable } from "@dnd-kit/core";
import type { CurriculumBoardEntryOut } from "@/lib/types";
import { DraggableCourseCard } from "./DraggableCourseCard";

export function SemesterColumn({
  semester, entries, onAddCourse,
}: {
  semester: number;
  entries: CurriculumBoardEntryOut[];
  onAddCourse: (semester: number) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: `semester-${semester}` });
  const credits = entries.reduce((sum, entry) => sum + entry.credits, 0);

  return (
    <div className="flex w-[224px] flex-none flex-col gap-[10px]">
      <div className="flex items-baseline justify-between">
        <div className={isOver ? "text-[15px] font-bold text-accent" : "text-[15px] font-bold text-navy"}>
          Semestre {semester}
        </div>
        <div className="text-[12.5px] text-text-tertiary">{credits} cr</div>
      </div>
      <div
        ref={setNodeRef}
        className={
          isOver
            ? "flex flex-col gap-2 rounded-[11px] border border-dashed border-accent bg-[#EAF2F9] p-2"
            : "flex flex-col gap-2"
        }
      >
        {entries.map((entry) => <DraggableCourseCard key={entry.course_id} entry={entry} />)}
        {isOver ? (
          <div className="h-[38px] rounded-card border border-dashed border-accent bg-surface
                           text-center text-[13px] font-medium leading-[38px] text-accent">
            Soltar aquí
          </div>
        ) : (
          <button
            onClick={() => onAddCourse(semester)}
            className="h-[38px] rounded-card border border-dashed border-border-dashed
                       text-[13px] font-medium text-text-secondary hover:border-accent
                       hover:text-accent"
          >
            + Materia
          </button>
        )}
      </div>
    </div>
  );
}
