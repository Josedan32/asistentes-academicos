import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AssistantMessage } from "./AssistantMessage";
import type { ChatMessage } from "@/lib/hooks/useChatStream";

function baseMessage(overrides: Partial<ChatMessage>): ChatMessage {
  return {
    id: 1, clientId: "1", role: "assistant", content: "aqui tienes", mode: "consulta",
    toolCalls: [
      {
        id: "t1", name: "search_course_material", arguments: { query: "matrices" },
        result: { fragments: [{ text: "1 1 1\n0 1 1", page: 3 }] }, duration_ms: 80, row_count: 1,
      },
    ],
    feedback: null,
    ...overrides,
  };
}

describe("AssistantMessage", () => {
  it("shows a search_course_material result as a plain tool card in consulta mode", () => {
    render(
      <AssistantMessage
        message={baseMessage({ mode: "consulta" })}
        avatarState="success"
        isStreaming={false}
      />
    );
    expect(screen.queryByText("Ejercicio del material del curso")).not.toBeInTheDocument();
  });

  it("shows a search_course_material result as an exercise citation in practica mode", () => {
    render(
      <AssistantMessage
        message={baseMessage({ mode: "practica" })}
        avatarState="success"
        isStreaming={false}
      />
    );
    expect(screen.getByText("Ejercicio del material del curso")).toBeInTheDocument();
  });

  it("renders each message by its own mode, regardless of any other message's mode", () => {
    const { rerender } = render(
      <AssistantMessage
        message={baseMessage({ id: 1, clientId: "1", mode: "practica" })}
        avatarState="success"
        isStreaming={false}
      />
    );
    expect(screen.getByText("Ejercicio del material del curso")).toBeInTheDocument();

    rerender(
      <AssistantMessage
        message={baseMessage({ id: 2, clientId: "2", mode: "consulta" })}
        avatarState="success"
        isStreaming={false}
      />
    );
    expect(screen.queryByText("Ejercicio del material del curso")).not.toBeInTheDocument();
  });
});
