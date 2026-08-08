import type { CurriculumBoardEntryOut } from "@/lib/types";

export function CourseCard({ entry }: { entry: CurriculumBoardEntryOut }) {
  const hasFooter = entry.prerequisites.length > 0 || entry.shared_program_count > 1;

  return (
    <div className="rounded-card border border-border bg-surface p-[11px_12px] hover:border-accent
                     hover:shadow-[0_3px_10px_rgba(11,33,64,.08)]">
      <div className="text-[14px] font-semibold leading-[1.3] text-navy">{entry.course_name}</div>
      <div className="flex justify-between pt-[5px]">
        <span className="font-mono text-[12px] text-text-tertiary">{entry.course_code}</span>
        <span className="text-[12px] font-medium text-text-secondary">{entry.credits} cr</span>
      </div>
      {hasFooter && (
        <div className="mt-2 flex flex-col gap-1 border-t border-border-row pt-[6px]">
          {entry.prerequisites.length > 0 && (
            <div className="text-[11.5px] text-accent-faint">
              Req: {entry.prerequisites.map((p) => p.course_name).join(", ")}
            </div>
          )}
          {entry.shared_program_count > 1 && (
            <div className="flex items-center gap-[5px] text-[11.5px] text-amber-text-muted">
              <span className="h-[6px] w-[6px] rounded-full bg-amber-accent" />
              Compartida · {entry.shared_program_count} carreras
            </div>
          )}
        </div>
      )}
    </div>
  );
}
