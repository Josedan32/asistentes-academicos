import type { MessageOut } from "./types";

export function mergeAssistantTurns(messages: MessageOut[]): MessageOut[] {
  const merged: MessageOut[] = [];
  for (const message of messages) {
    const previous = merged[merged.length - 1];
    if (message.role === "assistant" && previous?.role === "assistant") {
      previous.tool_calls = [...previous.tool_calls, ...message.tool_calls];
      previous.content = message.content || previous.content;
      previous.id = message.id;
      previous.feedback = message.feedback;
      continue;
    }
    merged.push({ ...message, tool_calls: [...message.tool_calls] });
  }
  return merged;
}
