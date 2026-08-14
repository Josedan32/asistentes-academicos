import type { MessageOut } from "./types";

/** A single agent turn can span several DB rows (one per tool-calling iteration, empty
 * content, plus a final row with the reply). Collapse consecutive assistant rows into one
 * so a reloaded conversation shows the same single bubble the live stream already renders. */
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
