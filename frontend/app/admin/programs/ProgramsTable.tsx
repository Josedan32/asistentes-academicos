"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { listPrograms } from "@/lib/api/programs";
import { createProgram, updateProgram, type ProgramPayload } from "@/lib/api/programs-admin";
import type { ProgramOut } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ProgramModal } from "./ProgramModal";

export function ProgramsTable() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const programsQuery = useQuery({ queryKey: ["admin-programs"], queryFn: listPrograms });
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [editing, setEditing] = useState<ProgramOut | null | "new">(null);

  const rows = useMemo(() => {
    return (programsQuery.data ?? []).filter((program) => {
      const matchesSearch = program.name.toLowerCase().includes(search.toLowerCase());
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" ? program.is_active : !program.is_active);
      return matchesSearch && matchesStatus;
    });
  }, [programsQuery.data, search, statusFilter]);

  async function handleSubmit(payload: ProgramPayload) {
    if (editing && editing !== "new") {
      await updateProgram(editing.id, payload);
    } else {
      await createProgram(payload);
    }
    await queryClient.invalidateQueries({ queryKey: ["admin-programs"] });
    setEditing(null);
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex h-[76px] flex-none items-center justify-between border-b border-border
                       bg-surface px-7">
        <div>
          <h1 className="m-0 text-[22px] font-bold text-navy">Carreras</h1>
          <div className="text-[13.5px] text-text-secondary">
            {(programsQuery.data ?? []).filter((p) => p.is_active).length} programas activos
          </div>
        </div>
        <Button onClick={() => setEditing("new")}
                className="h-10 rounded-control bg-navy px-[18px] text-[14px] font-semibold text-white">
          Nueva carrera
        </Button>
      </div>

      <div className="flex-1 overflow-auto p-7">
        <div className="flex gap-[10px] pb-4">
          <Input placeholder="Buscar carrera" value={search}
                 onChange={(event) => setSearch(event.target.value)}
                 className="h-[38px] w-[280px] rounded-control border-border-control px-3 text-[14px]" />
          <select value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}
                  className="h-[38px] rounded-control border border-border-control bg-surface px-[10px] text-[14px]">
            <option value="all">Todos los estados</option>
            <option value="active">Activa</option>
            <option value="inactive">Inactiva</option>
          </select>
        </div>

        <div className="overflow-hidden rounded-card-lg border border-border bg-surface">
          <table className="w-full border-collapse text-[14.5px] text-text-body">
            <thead>
              <tr className="bg-[#F5F7F9] text-left">
                <th className="border-b border-border p-[12px_18px] text-[12px] font-semibold
                                uppercase tracking-[.08em] text-text-secondary">Código</th>
                <th className="border-b border-border p-[12px_18px] text-[12px] font-semibold
                                uppercase tracking-[.08em] text-text-secondary">Nombre</th>
                <th className="border-b border-border p-[12px_18px] text-[12px] font-semibold
                                uppercase tracking-[.08em] text-text-secondary">Semestres</th>
                <th className="border-b border-border p-[12px_18px] text-[12px] font-semibold
                                uppercase tracking-[.08em] text-text-secondary">Materias</th>
                <th className="border-b border-border p-[12px_18px] text-[12px] font-semibold
                                uppercase tracking-[.08em] text-text-secondary">Estado</th>
                <th className="border-b border-border p-[12px_18px]" />
              </tr>
            </thead>
            <tbody>
              {rows.map((program) => (
                <tr key={program.id} className="border-b border-border-row">
                  <td className="p-[13px_18px] font-mono text-[14px] font-medium">{program.code}</td>
                  <td className="p-[13px_18px] font-medium">{program.name}</td>
                  <td className="p-[13px_18px]">{program.semester_count}</td>
                  <td className="p-[13px_18px]">{program.course_count}</td>
                  <td className="p-[13px_18px]">
                    <span className={
                      program.is_active
                        ? "rounded-pill bg-success-bg px-[10px] py-[3px] text-[12px] font-semibold text-success-text"
                        : "rounded-pill bg-inactive-bg px-[10px] py-[3px] text-[12px] font-semibold text-inactive-text"
                    }>
                      {program.is_active ? "Activa" : "Inactiva"}
                    </span>
                  </td>
                  <td className="p-[13px_18px] text-right">
                    <a href="#" onClick={(event) => { event.preventDefault(); router.push("/admin/curriculum"); }}
                       className="pr-[14px] text-[14px] font-medium text-accent">Malla</a>
                    <a href="#" onClick={(event) => { event.preventDefault(); setEditing(program); }}
                       className="text-[14px] font-medium text-accent">Editar</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <ProgramModal
        key={editing === "new" ? "new" : (editing?.id ?? "closed")}
        open={editing !== null}
        program={editing === "new" ? null : editing}
        onClose={() => setEditing(null)}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
