"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createCourse, listCourses, updateCourse, type CoursePayload } from "@/lib/api/courses-admin";
import type { CourseWithUsageOut } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CourseModal } from "./CourseModal";

export function CoursesTable() {
  const queryClient = useQueryClient();
  const coursesQuery = useQuery({ queryKey: ["admin-courses"], queryFn: listCourses });
  const [search, setSearch] = useState("");
  const [areaFilter, setAreaFilter] = useState("all");
  const [usageFilter, setUsageFilter] = useState<"all" | "unassigned">("all");
  const [editing, setEditing] = useState<CourseWithUsageOut | null | "new">(null);

  const areas = useMemo(
    () => Array.from(new Set((coursesQuery.data ?? []).map((course) => course.area))),
    [coursesQuery.data]
  );

  const rows = useMemo(() => {
    return (coursesQuery.data ?? []).filter((course) => {
      const matchesSearch =
        course.name.toLowerCase().includes(search.toLowerCase()) ||
        course.code.toLowerCase().includes(search.toLowerCase());
      const matchesArea = areaFilter === "all" || course.area === areaFilter;
      const matchesUsage = usageFilter === "all" || course.placements.length === 0;
      return matchesSearch && matchesArea && matchesUsage;
    });
  }, [coursesQuery.data, search, areaFilter, usageFilter]);

  async function handleSubmit(payload: CoursePayload) {
    if (editing && editing !== "new") {
      await updateCourse(editing.id, payload);
    } else {
      await createCourse(payload);
    }
    await queryClient.invalidateQueries({ queryKey: ["admin-courses"] });
    setEditing(null);
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex h-[76px] flex-none items-center justify-between border-b border-border
                       bg-surface px-7">
        <div>
          <h1 className="m-0 text-[22px] font-bold text-navy">Materias</h1>
          <div className="text-[13.5px] text-text-secondary">
            Catálogo global · una materia puede pertenecer a varias carreras
          </div>
        </div>
        <Button onClick={() => setEditing("new")}
                className="h-10 rounded-control bg-navy px-[18px] text-[14px] font-semibold text-white">
          Nueva materia
        </Button>
      </div>

      <div className="flex-1 overflow-auto p-7">
        <div className="flex gap-[10px] pb-4">
          <Input placeholder="Buscar por nombre o código" value={search}
                 onChange={(event) => setSearch(event.target.value)}
                 className="h-[38px] w-[300px] rounded-control border-border-control px-3 text-[14px]" />
          <select aria-label="Área" value={areaFilter}
                  onChange={(event) => setAreaFilter(event.target.value)}
                  className="h-[38px] rounded-control border border-border-control bg-surface px-[10px] text-[14px]">
            <option value="all">Todas las áreas</option>
            {areas.map((area) => <option key={area} value={area}>{area}</option>)}
          </select>
          <select aria-label="Uso" value={usageFilter}
                  onChange={(event) => setUsageFilter(event.target.value as typeof usageFilter)}
                  className="h-[38px] rounded-control border border-border-control bg-surface px-[10px] text-[14px]">
            <option value="all">Usada en cualquier carrera</option>
            <option value="unassigned">Sin asignar a ninguna malla</option>
          </select>
        </div>

        <div className="overflow-hidden rounded-card-lg border border-border bg-surface">
          <table className="w-full border-collapse text-[14.5px] text-text-body">
            <thead>
              <tr className="bg-[#F5F7F9] text-left">
                <th className="border-b border-border p-[12px_18px] text-[12px] font-semibold
                                uppercase tracking-[.08em] text-text-secondary">Código</th>
                <th className="border-b border-border p-[12px_18px] text-[12px] font-semibold
                                uppercase tracking-[.08em] text-text-secondary">Materia</th>
                <th className="border-b border-border p-[12px_18px] text-[12px] font-semibold
                                uppercase tracking-[.08em] text-text-secondary">Área</th>
                <th className="border-b border-border p-[12px_18px] text-[12px] font-semibold
                                uppercase tracking-[.08em] text-text-secondary">Créditos</th>
                <th className="border-b border-border p-[12px_18px] text-[12px] font-semibold
                                uppercase tracking-[.08em] text-text-secondary">En mallas</th>
                <th className="border-b border-border p-[12px_18px]" />
              </tr>
            </thead>
            <tbody>
              {rows.map((course) => (
                <tr key={course.id} className="border-b border-border-row">
                  <td className="p-[13px_18px] font-mono text-[14px] font-medium">{course.code}</td>
                  <td className="p-[13px_18px] font-medium">{course.name}</td>
                  <td className="p-[13px_18px] text-text-secondary">{course.area}</td>
                  <td className="p-[13px_18px]">{course.default_credits}</td>
                  <td className="p-[13px_18px]">
                    {course.placements.length === 0 ? (
                      <span className="text-text-tertiary">Sin asignar</span>
                    ) : (
                      `${course.placements.length} ${course.placements.length === 1 ? "carrera" : "carreras"}`
                    )}
                  </td>
                  <td className="p-[13px_18px] text-right">
                    <a href="#" onClick={(event) => { event.preventDefault(); setEditing(course); }}
                       className="text-[14px] font-medium text-accent">Editar</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <CourseModal
        key={editing === "new" ? "new" : (editing?.id ?? "closed")}
        open={editing !== null}
        course={editing === "new" ? null : editing}
        onClose={() => setEditing(null)}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
