"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listPrograms } from "@/lib/api/programs";
import { getCurriculumBoard } from "@/lib/api/curriculum-admin";
import { groupBoardBySemester } from "@/lib/group-board-by-semester";
import { Button } from "@/components/ui/button";
import { SemesterColumn } from "./SemesterColumn";

export function CurriculumBoard() {
  const programsQuery = useQuery({ queryKey: ["admin-programs"], queryFn: listPrograms });
  const [programId, setProgramId] = useState<number | null>(null);
  const [assignSemester, setAssignSemester] = useState<number | null>(null);

  const activeProgramId = programId ?? programsQuery.data?.[0]?.id ?? null;
  const activeProgram = programsQuery.data?.find((program) => program.id === activeProgramId);

  const boardQuery = useQuery({
    queryKey: ["curriculum-board", activeProgramId],
    queryFn: () => getCurriculumBoard(activeProgramId as number),
    enabled: activeProgramId !== null,
  });

  const grouped = useMemo(
    () => groupBoardBySemester(boardQuery.data ?? [], activeProgram?.semester_count ?? 0),
    [boardQuery.data, activeProgram?.semester_count]
  );
  const totalCredits = (boardQuery.data ?? []).reduce((sum, entry) => sum + entry.credits, 0);

  return (
    <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
      <div className="flex flex-none items-center justify-between gap-5 border-b border-border
                       bg-surface p-[16px_28px]">
        <div className="flex items-center gap-4">
          <div>
            <div className="pb-1 text-[11px] font-semibold uppercase tracking-[.14em]
                             text-text-tertiary">
              Malla de
            </div>
            <select
              value={activeProgramId ?? ""}
              onChange={(event) => setProgramId(Number(event.target.value))}
              className="h-[42px] min-w-[280px] rounded-control border border-border-control
                         px-3 text-[16px] font-semibold text-navy"
            >
              {(programsQuery.data ?? []).map((program) => (
                <option key={program.id} value={program.id}>{program.name}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-[22px] pl-2">
            <div>
              <div className="text-[22px] font-bold text-navy">{boardQuery.data?.length ?? 0}</div>
              <div className="text-[12.5px] text-text-secondary">materias</div>
            </div>
            <div>
              <div className="text-[22px] font-bold text-navy">{totalCredits}</div>
              <div className="text-[12.5px] text-text-secondary">créditos</div>
            </div>
            <div>
              <div className="text-[22px] font-bold text-navy">
                {activeProgram?.semester_count ?? 0}
              </div>
              <div className="text-[12.5px] text-text-secondary">semestres</div>
            </div>
          </div>
        </div>
        <div className="flex gap-[9px]">
          <Button variant="outline"
                  className="h-10 rounded-control border-border-control px-4 text-[14px] font-semibold">
            Ver prerrequisitos
          </Button>
          <Button onClick={() => setAssignSemester(1)}
                  className="h-10 rounded-control bg-navy px-[18px] text-[14px] font-semibold text-white">
            Asignar materia
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-[22px_28px]">
        <div className="flex min-w-max items-start gap-[14px]">
          {[...grouped.entries()].map(([semester, entries]) => (
            <SemesterColumn key={semester} semester={semester} entries={entries}
                             onAddCourse={setAssignSemester} />
          ))}
        </div>
      </div>

      {/* Task D5 replaces this comment with the "Asignar materia" Sheet, driven by
          `assignSemester` (non-null when open) and `activeProgramId`. */}
    </div>
  );
}
