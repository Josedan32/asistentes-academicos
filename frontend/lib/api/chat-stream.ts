import { getStoredToken } from "./client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface SSEEvent {
  event: string;
  data: Record<string, any>;
}

export function parseSSEChunk(buffer: string): { events: SSEEvent[]; remainder: string } {
  const segments = buffer.split("\n\n");
  const remainder = segments.pop() ?? "";
  const events: SSEEvent[] = [];

  for (const segment of segments) {
    if (!segment.trim()) continue;
    let eventName = "message";
    let dataLine = "";
    for (const line of segment.split("\n")) {
      if (line.startsWith("event: ")) eventName = line.slice("event: ".length);
      else if (line.startsWith("data: ")) dataLine = line.slice("data: ".length);
    }
    if (dataLine) events.push({ event: eventName, data: JSON.parse(dataLine) });
  }

  return { events, remainder };
}

export interface ChatStreamPayload {
  conversation_id: number | null;
  course_id: number | null;
  message: string;
}

export async function streamChat(
  payload: ChatStreamPayload, onEvent: (event: SSEEvent) => void, signal: AbortSignal
): Promise<void> {
  const token = getStoredToken();
  const headers = new Headers({ "Content-Type": "application/json" });
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
    method: "POST", headers, body: JSON.stringify(payload), signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(`Chat stream request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parsed = parseSSEChunk(buffer);
    buffer = parsed.remainder;
    for (const event of parsed.events) onEvent(event);
  }
}
