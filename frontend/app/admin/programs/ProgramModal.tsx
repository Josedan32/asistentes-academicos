"use client";

import { useState } from "react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ProgramOut } from "@/lib/types";
import type { ProgramPayload } from "@/lib/api/programs-admin";

export function ProgramModal({
  open, program, onClose, onSubmit,
}: {
  open: boolean;
  program: ProgramOut | null;
  onClose: () => void;
  onSubmit: (payload: ProgramPayload) => void;
}) {
  const [name, setName] = useState(program?.name ?? "");
  const [code, setCode] = useState(program?.code ?? "");
  const [semesterCount, setSemesterCount] = useState(program?.semester_count ?? 10);
  const [isActive, setIsActive] = useState(program?.is_active ?? true);

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="w-[480px] rounded-container p-[26px]">
        <DialogHeader>
          <DialogTitle className="text-[20px] font-bold text-navy">
            {program ? "Editar carrera" : "Nueva carrera"}
          </DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-[18px]">
          <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
            Nombre
            <Input value={name} onChange={(event) => setName(event.target.value)}
                   className="h-[42px] rounded-control border-border-control px-3 text-[15px]" />
          </label>
          <div className="grid grid-cols-2 gap-[14px]">
            <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
              Código
              <Input value={code} onChange={(event) => setCode(event.target.value)}
                     className="h-[42px] rounded-control border-border-control px-3 text-[15px]" />
            </label>
            <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
              Semestres
              <Input type="number" min={1} max={12} value={semesterCount}
                     onChange={(event) => setSemesterCount(Number(event.target.value))}
                     className="h-[42px] rounded-control border-border-control px-3 text-[15px]" />
            </label>
          </div>
          <label className="flex items-center gap-[9px] text-[14px] text-text-label">
            <input type="checkbox" checked={isActive}
                   onChange={(event) => setIsActive(event.target.checked)}
                   className="h-[15px] w-[15px] accent-accent" />
            Carrera activa
          </label>
          <div className="flex justify-end gap-[9px] pt-1">
            <Button variant="outline" onClick={onClose}
                    className="h-10 rounded-control border-border-control px-4 text-[14px] font-semibold">
              Cancelar
            </Button>
            <Button
              onClick={() =>
                onSubmit({ code, name, semester_count: semesterCount, is_active: isActive })
              }
              className="h-10 rounded-control bg-navy px-[18px] text-[14px] font-semibold text-white"
            >
              Guardar
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
