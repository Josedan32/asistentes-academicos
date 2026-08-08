import { apiFetch } from "./client";
import type { ProgramOut } from "../types";

export interface ProgramPayload {
  code: string;
  name: string;
  semester_count: number;
  is_active: boolean;
}

export function createProgram(payload: ProgramPayload): Promise<ProgramOut> {
  return apiFetch<ProgramOut>("/api/v1/admin/programs", {
    method: "POST", body: JSON.stringify(payload),
  });
}

export function updateProgram(id: number, payload: ProgramPayload): Promise<ProgramOut> {
  return apiFetch<ProgramOut>(`/api/v1/admin/programs/${id}`, {
    method: "PATCH", body: JSON.stringify(payload),
  });
}
