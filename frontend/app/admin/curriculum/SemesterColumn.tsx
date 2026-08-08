import type { CurriculumBoardEntryOut } from "@/lib/types";
import { CourseCard } from "./CourseCard";

export function SemesterColumn({
  semester, entries, onAddCourse,
}: {
  semester: number;
  entries: CurriculumBoardEntryOut[];
  onAddCourse: (semester: number) => void;
}) {
  const credits = entries.reduce((sum, entry) => sum + entry.credits, 0);

  return (
    <div className="flex w-[224px] flex-none flex-col gap-[10px]">
      <div className="flex items-baseline justify-between">
        <div className="text-[15px] font-bold text-navy">Semestre {semester}</div>
        <div className="text-[12.5px] text-text-tertiary">{credits} cr</div>
      </div>
      <div className="flex flex-col gap-2">
        {entries.map((entry) => <CourseCard key={entry.course_id} entry={entry} />)}
        <button
          onClick={() => onAddCourse(semester)}
          className="h-[38px] rounded-card border border-dashed border-border-dashed
                     text-[13px] font-medium text-text-secondary hover:border-accent
                     hover:text-accent"
        >
          + Materia
        </button>
      </div>
    </div>
  );
}
