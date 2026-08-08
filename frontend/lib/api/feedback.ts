import { apiFetch } from "./client";

export interface FeedbackPayload {
  value: "up" | "down";
  comment: string | null;
}

export function submitFeedback(
  messageId: number, payload: FeedbackPayload
): Promise<{ id: number }> {
  return apiFetch<{ id: number }>(`/api/v1/chat/messages/${messageId}/feedback`, {
    method: "POST", body: JSON.stringify(payload),
  });
}
