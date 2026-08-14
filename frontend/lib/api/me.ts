import { apiFetch } from "./client";
import type { EnrollmentOut, MeOut } from "../types";

export function getMe(): Promise<MeOut> {
  return apiFetch<MeOut>("/api/v1/me");
}

export function listMyEnrollments(): Promise<EnrollmentOut[]> {
  return apiFetch<EnrollmentOut[]>("/api/v1/me/enrollments");
}

export function getChatModel(): Promise<{ model: string }> {
  return apiFetch<{ model: string }>("/api/v1/chat/model");
}
