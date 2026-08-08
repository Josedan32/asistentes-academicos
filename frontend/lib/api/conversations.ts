import { apiFetch } from "./client";
import type { ConversationDetailOut, ConversationSummaryOut } from "../types";

export function listConversations(): Promise<ConversationSummaryOut[]> {
  return apiFetch<ConversationSummaryOut[]>("/api/v1/chat/conversations");
}

export function getConversation(id: number): Promise<ConversationDetailOut> {
  return apiFetch<ConversationDetailOut>(`/api/v1/chat/conversations/${id}`);
}
