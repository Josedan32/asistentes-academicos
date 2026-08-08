"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createCourse, listCourses } from "@/lib/api/courses-admin";
import { assignCourseToCurriculum } from "@/lib/api/curriculum-admin";
import { classifyCourseMatch } from "@/lib/classify-course-match";
import type { CourseWithUsageOut, CurriculumBoardEntryOut, ProgramOut } from "@/lib/types";
import { CourseModal } from "../courses/CourseModal";

export function AssignCoursePanel({
  open, program, targetSemester, earlierSemesterCourses, onClose,
}: {
  open: boolean;
  program: ProgramOut;
  targetSemester: number;
  earlierSemesterCourses: CurriculumBoardEntryOut[];
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const coursesQuery = useQuery({ queryKey: ["admin-courses"], queryFn: listCourses });
  const [search, setSearch] = useState("");
  const [selectedCourse, setSelectedCourse] = useState<CourseWithUsageOut | null>(null);
  const [semester, setSemester] = useState(targetSemester);
  const [credits, setCredits] = useState(3);
  const [prerequisiteIds, setPrerequisiteIds] = useState<number[]>([]);
  const [creatingCourse, setCreatingCourse] = useState(false);

  const results = useMemo(() => {
    if (!search.trim()) return [];
    const needle = search.toLowerCase();
    return (coursesQuery.data ?? []).filter(
      (course) =>
        course.name.toLowerCase().includes(needle) || course.code.toLowerCase().includes(needle)
    );
  }, [coursesQuery.data, search]);

  const earlierBySemester = useMemo(() => {
    const grouped = new Map<number, CurriculumBoardEntryOut[]>();
    for (const entry of earlierSemesterCourses) {
      if (entry.semester >= targetSemester) continue;
      if (!grouped.has(entry.semester)) grouped.set(entry.semester, []);
      grouped.get(entry.semester)!.push(entry);
    }
    return [...grouped.entries()].sort((a, b) => b[0] - a[0]);
  }, [earlierSemesterCourses, targetSemester]);

  function selectCourse(course: CourseWithUsageOut) {
    setSelectedCourse(course);
    setCredits(course.default_credits);
  }

  async function handleSubmit() {
    if (!selectedCourse) return;
    await assignCourseToCurriculum(program.id, {
      course_id: selectedCourse.id, semester, credits, prerequisite_course_ids: prerequisiteIds,
    });
    await queryClient.invalidateQueries({ queryKey: ["curriculum-board", program.id] });
    onClose();
  }

  async function handleCreateCourse(payload: {
    code: string; name: string; area: string; default_credits: number;
  }) {
    const created = await createCourse(payload);
    await queryClient.invalidateQueries({ queryKey: ["admin-courses"] });
    selectCourse({ ...created, placements: [] });
    setCreatingCourse(false);
  }

  return (
    <>
      <Sheet open={open} onOpenChange={(next) => !next && onClose()}>
        <SheetContent side="right" className="w-[432px] p-0">
          <div className="flex h-full flex-col">
            <div className="flex items-start justify-between gap-3 border-b border-border
                             p-[20px_22px_16px]">
              <div>
                <SheetTitle className="text-[19px] font-bold text-navy">
                  Asignar materia
                </SheetTitle>
                <div className="pt-[3px] text-[13.5px] text-text-secondary">
                  {program.name} · semestre {targetSemester}
                </div>
              </div>
              <button onClick={onClose} aria-label="Cerrar"
                      className="flex h-[30px] w-[30px] items-center justify-center
                                 rounded-[7px] border border-border text-text-secondary">
                <X className="h-[14px] w-[14px]" />
              </button>
            </div>

            <div className="flex flex-1 flex-col gap-5 overflow-auto p-[18px_22px]">
              <div className="flex flex-col gap-[9px]">
                <div className="text-[12px] font-semibold uppercase tracking-[.1em]
                                 text-text-tertiary">
                  Buscar en el catálogo global
                </div>
                <Input value={search} onChange={(event) => setSearch(event.target.value)}
                       placeholder="Nombre o código"
                       className="h-[42px] rounded-control border-border-control px-3 text-[15px]" />
              </div>

              <div className="flex flex-col gap-2">
                {results.map((course) => {
                  const match = classifyCourseMatch(course, program.id);

                  if (match.status === "in-program") {
                    return (
                      <div key={course.id}
                           className="flex items-center justify-between gap-[10px] rounded-card-lg
                                      border border-border p-[13px_14px]">
                        <div>
                          <div className="text-[15px] font-semibold text-navy">{course.name}</div>
                          <div className="pt-[3px] font-mono text-[12.5px] text-text-secondary">
                            {course.code} · {course.default_credits} créditos
                          </div>
                        </div>
                        <span className="whitespace-nowrap text-[12.5px] text-text-tertiary">
                          Ya en semestre {match.semester}
                        </span>
                      </div>
                    );
                  }

                  if (match.status === "shared") {
                    return (
                      <button key={course.id} onClick={() => selectCourse(course)}
                              className="flex flex-col gap-[9px] rounded-card-lg border-2
                                         border-accent bg-[#F5F9FD] p-[13px_14px] text-left">
                        <div className="flex items-start justify-between gap-[10px]">
                          <div>
                            <div className="text-[15px] font-semibold text-navy">
                              {course.name}
                            </div>
                            <div className="pt-[3px] font-mono text-[12.5px] text-text-secondary">
                              {course.code} · {course.default_credits} créditos
                            </div>
                          </div>
                          <span className="whitespace-nowrap rounded-pill bg-accent px-[10px]
                                            py-[3px] text-[11.5px] font-semibold text-white">
                            Ya existe
                          </span>
                        </div>
                        <div className="flex gap-[9px] rounded-control border border-amber-border
                                         bg-amber-bg p-[10px_12px]">
                          <span className="h-[18px] w-[18px] flex-none rounded-full
                                            bg-amber-accent text-center text-[11px]
                                            font-semibold leading-[18px] text-white">
                            !
                          </span>
                          <div className="text-[13px] leading-[1.5] text-amber-text">
                            También está en{" "}
                            <strong className="font-semibold">
                              {match.otherProgramName}, semestre {match.otherSemester}
                            </strong>
                            . Úsala tal cual para que el material y el asistente se compartan
                            entre carreras; no crees un duplicado.
                          </div>
                        </div>
                      </button>
                    );
                  }

                  return (
                    <button key={course.id} onClick={() => selectCourse(course)}
                            className="flex items-center justify-between gap-[10px]
                                       rounded-card-lg border border-border p-[13px_14px]
                                       text-left hover:border-accent">
                      <div>
                        <div className="text-[15px] font-semibold text-navy">{course.name}</div>
                        <div className="pt-[3px] font-mono text-[12.5px] text-text-secondary">
                          {course.code} · {course.default_credits} créditos
                        </div>
                      </div>
                      <span className="whitespace-nowrap text-[12.5px] text-text-tertiary">
                        Sin asignar
                      </span>
                    </button>
                  );
                })}

                {search.trim() && (
                  <button onClick={() => setCreatingCourse(true)}
                          className="h-10 rounded-card border border-dashed border-border-dashed
                                     text-[13.5px] font-medium text-text-secondary
                                     hover:border-accent hover:text-accent">
                    Ninguna coincide · crear materia nueva
                  </button>
                )}
              </div>

              {selectedCourse && (
                <>
                  <div className="h-px bg-border" />
                  <div className="flex flex-col gap-3">
                    <label className="flex flex-col gap-[7px] text-[13px] font-semibold
                                       text-text-label">
                      Semestre en esta malla
                      <select value={semester}
                              onChange={(event) => setSemester(Number(event.target.value))}
                              className="h-[42px] rounded-control border border-border-control
                                         px-3 text-[15px]">
                        {Array.from({ length: program.semester_count }, (_, index) => index + 1).map(
                          (value) => <option key={value} value={value}>Semestre {value}</option>
                        )}
                      </select>
                    </label>
                    <label className="flex flex-col gap-[7px] text-[13px] font-semibold
                                       text-text-label">
                      Créditos en esta carrera
                      <Input type="number" min={1} max={12} value={credits}
                             onChange={(event) => setCredits(Number(event.target.value))}
                             className="h-[42px] w-[120px] rounded-control border-border-control
                                        px-3 text-[15px]" />
                    </label>
                  </div>

                  <div className="flex flex-col gap-[10px]">
                    <div className="flex items-baseline justify-between">
                      <div className="text-[13px] font-semibold text-text-label">
                        Prerrequisitos
                      </div>
                      <div className="text-[12.5px] text-text-tertiary">
                        Solo materias de semestres 1 a {targetSemester - 1}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-[7px]">
                      {prerequisiteIds.map((id) => {
                        const course = earlierSemesterCourses.find(
                          (entry) => entry.course_id === id
                        );
                        if (!course) return null;
                        return (
                          <span key={id}
                                className="flex items-center gap-[7px] rounded-pill bg-navy
                                           px-[11px] py-[5px] text-[13px] font-medium text-white">
                            {course.course_name}
                            <span className="cursor-pointer opacity-60 hover:opacity-100"
                                  role="button" aria-label={`Quitar ${course.course_name}`}
                                  onClick={() =>
                                    setPrerequisiteIds((prev) => prev.filter((p) => p !== id))
                                  }>
                              <X className="h-3 w-3" />
                            </span>
                          </span>
                        );
                      })}
                    </div>
                    <div className="max-h-[172px] overflow-auto rounded-card-lg border
                                     border-border">
                      {earlierBySemester.map(([sem, entries]) => (
                        <div key={sem}>
                          <div className="bg-[#F5F7F9] p-[9px_12px] text-[11px] font-semibold
                                           uppercase tracking-[.1em] text-text-tertiary">
                            Semestre {sem}
                          </div>
                          {entries.map((entry) => (
                            <label key={entry.course_id}
                                   className="flex items-center gap-[9px] p-[9px_12px]
                                              text-[14px] text-text-body hover:bg-[#F5F9FD]">
                              <input
                                type="checkbox"
                                checked={prerequisiteIds.includes(entry.course_id)}
                                onChange={(event) =>
                                  setPrerequisiteIds((prev) =>
                                    event.target.checked
                                      ? [...prev, entry.course_id]
                                      : prev.filter((id) => id !== entry.course_id)
                                  )
                                }
                                className="accent-accent"
                              />
                              {entry.course_name}
                            </label>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="flex justify-end gap-[9px] border-t border-border p-[16px_22px]">
              <Button variant="outline" onClick={onClose}
                      className="h-[42px] rounded-control border-border-control px-4 text-[14px]
                                 font-semibold">
                Cancelar
              </Button>
              <Button onClick={handleSubmit} disabled={!selectedCourse}
                      className="h-[42px] rounded-control bg-navy px-5 text-[14px] font-semibold
                                 text-white">
                Asignar a semestre {semester}
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>

      <CourseModal open={creatingCourse} course={null} onClose={() => setCreatingCourse(false)}
                   onSubmit={handleCreateCourse} />
    </>
  );
}
