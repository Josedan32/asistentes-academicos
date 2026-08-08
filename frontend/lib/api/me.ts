import { apiFetch } from "./client";
import type { MeOut } from "../types";

export function getMe(): Promise<MeOut> {
  return apiFetch<MeOut>("/api/v1/me");
}

export function getChatModel(): Promise<{ model: string }> {
  return apiFetch<{ model: string }>("/api/v1/chat/model");
}
