"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { CourseWithUsageOut } from "@/lib/types";
import type { CoursePayload } from "@/lib/api/courses-admin";

const AREAS = ["Ciencias básicas", "Programación", "Sociohumanística"];

export function CourseModal({
  open, course, onClose, onSubmit,
}: {
  open: boolean;
  course: CourseWithUsageOut | null;
  onClose: () => void;
  onSubmit: (payload: CoursePayload) => void;
}) {
  const [name, setName] = useState(course?.name ?? "");
  const [code, setCode] = useState(course?.code ?? "");
  const [credits, setCredits] = useState(course?.default_credits ?? 4);
  const [area, setArea] = useState(course?.area ?? AREAS[0]);

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="w-[520px] rounded-container p-[26px]">
        <DialogHeader>
          <DialogTitle className="text-[20px] font-bold text-navy">
            {course ? "Editar materia" : "Nueva materia"}
          </DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-[18px]">
          <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
            Nombre
            <Input value={name} onChange={(event) => setName(event.target.value)}
                   className="h-[42px] rounded-control border-border-control px-3 text-[15px]" />
          </label>
          <div className="grid grid-cols-3 gap-[14px]">
            <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
              Código
              <Input value={code} onChange={(event) => setCode(event.target.value)}
                     className="h-[42px] rounded-control border-border-control px-3 text-[15px]" />
            </label>
            <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
              Créditos
              <Input type="number" min={1} max={12} value={credits}
                     onChange={(event) => setCredits(Number(event.target.value))}
                     className="h-[42px] rounded-control border-border-control px-3 text-[15px]" />
            </label>
            <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
              Área
              <select value={area} onChange={(event) => setArea(event.target.value)}
                      className="h-[42px] rounded-control border border-border-control px-[10px] text-[15px]">
                {AREAS.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </label>
          </div>
          <div className="rounded-control bg-[#F5F7F9] p-[12px_14px] text-[13.5px] leading-[1.5]
                           text-text-secondary">
            Las materias son independientes de la carrera. Se asignan a un semestre desde{" "}
            <a href="/admin/curriculum" className="font-semibold text-accent">Malla curricular</a>.
          </div>
          <div className="flex justify-end gap-[9px]">
            <Button variant="outline" onClick={onClose}
                    className="h-10 rounded-control border-border-control px-4 text-[14px] font-semibold">
              Cancelar
            </Button>
            <Button
              onClick={() => onSubmit({ code, name, area, default_credits: credits })}
              className="h-10 rounded-control bg-navy px-[18px] text-[14px] font-semibold text-white"
            >
              {course ? "Guardar" : "Crear materia"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
