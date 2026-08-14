"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { CourseWithUsageOut } from "@/lib/types";
import type { CoursePayload } from "@/lib/api/courses-admin";
import { deleteMaterial, listMaterials, uploadMaterial } from "@/lib/api/materials-admin";

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
  const [materialError, setMaterialError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const queryClient = useQueryClient();
  const materialsQuery = useQuery({
    queryKey: ["course-materials", course?.id],
    queryFn: () => listMaterials(course!.id),
    enabled: course !== null,
  });

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || course === null) return;
    setIsUploading(true);
    try {
      await uploadMaterial(course.id, file);
      await queryClient.invalidateQueries({ queryKey: ["course-materials", course.id] });
      setMaterialError(null);
    } catch {
      setMaterialError("No se pudo subir el archivo. Verifica el formato (solo PDF o Word).");
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  }

  async function handleDeleteMaterial(materialId: number) {
    try {
      await deleteMaterial(materialId);
      await queryClient.invalidateQueries({ queryKey: ["course-materials", course?.id] });
      setMaterialError(null);
    } catch {
      setMaterialError("No se pudo eliminar el material.");
    }
  }

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
          {course && (
            <div className="flex flex-col gap-[10px]">
              <div className="text-[13px] font-semibold text-text-label">Material de estudio</div>
              <div className="flex flex-col gap-2">
                {(materialsQuery.data ?? []).map((material) => (
                  <div key={material.id}
                       className="flex items-center justify-between rounded-control border
                                  border-border-control px-3 py-2 text-[14px]">
                    <span className="truncate">{material.filename}</span>
                    <button onClick={() => handleDeleteMaterial(material.id)}
                            className="text-[13px] font-medium text-error-accent">
                      Eliminar
                    </button>
                  </div>
                ))}
              </div>
              {materialError && (
                <div className="text-[13px] font-medium text-error-accent">{materialError}</div>
              )}
              {isUploading && (
                <div className="text-[13px] font-medium text-text-secondary">
                  Subiendo y procesando el material... esto puede tardar varios minutos, no
                  cierres esta ventana.
                </div>
              )}
              <label className={`flex h-10 items-center justify-center rounded-control border
                                  border-dashed border-border-dashed text-[13px] font-medium ${
                                    isUploading
                                      ? "cursor-not-allowed text-text-tertiary"
                                      : "cursor-pointer text-text-secondary hover:border-accent hover:text-accent"
                                  }`}>
                {isUploading ? "Procesando..." : "+ Subir PDF o Word"}
                <input type="file" accept=".pdf,.docx" onChange={handleUpload}
                       disabled={isUploading} className="hidden" />
              </label>
            </div>
          )}
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
