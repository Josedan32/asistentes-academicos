import { describe, expect, it } from "vitest";
import { mergeAssistantTurns } from "./merge-assistant-turns";
import type { MessageOut, ToolCallOut } from "./types";

function toolCall(overrides: Partial<ToolCallOut>): ToolCallOut {
  return {
    id: 1, name: "search_course_material", arguments: {}, result: null,
    duration_ms: 10, row_count: 1, sequence: 1, ...overrides,
  };
}

function message(overrides: Partial<MessageOut>): MessageOut {
  return { id: 1, role: "assistant", content: "", tool_calls: [], feedback: null, ...overrides };
}

describe("mergeAssistantTurns", () => {
  it("merges an empty-content tool-call row into the final reply that follows it", () => {
    const merged = mergeAssistantTurns([
      message({ role: "user", id: 1, content: "hola" }),
      message({ id: 2, content: "", tool_calls: [toolCall({ id: 10 })] }),
      message({ id: 3, content: "Aqui tienes." }),
    ]);

    expect(merged).toHaveLength(2);
    expect(merged[1].id).toBe(3);
    expect(merged[1].content).toBe("Aqui tienes.");
    expect(merged[1].tool_calls.map((t) => t.id)).toEqual([10]);
  });

  it("leaves independent turns in separate messages", () => {
    const merged = mergeAssistantTurns([
      message({ role: "user", id: 1, content: "hola" }),
      message({ id: 2, content: "primera respuesta" }),
      message({ role: "user", id: 3, content: "otra pregunta" }),
      message({ id: 4, content: "segunda respuesta" }),
    ]);

    expect(merged.map((m) => m.content)).toEqual([
      "hola", "primera respuesta", "otra pregunta", "segunda respuesta",
    ]);
  });

  it("does not mutate the original messages", () => {
    const original = [message({ id: 2, content: "", tool_calls: [toolCall({ id: 10 })] })];
    mergeAssistantTurns(original);
    expect(original[0].content).toBe("");
  });
});
