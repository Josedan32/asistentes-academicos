import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ToolCallCard } from "./ToolCallCard";

const toolCall = {
  id: "1", name: "get_prerequisites", arguments: { course: "Base de Datos 2" },
  result: { prerequisites: [{ course_name: "Base de Datos 1" }] },
  duration_ms: 420, row_count: 1,
};

describe("ToolCallCard", () => {
  it("shows the Spanish description and duration", () => {
    render(<ToolCallCard toolCall={toolCall} />);
    expect(screen.getByText('Consultando prerrequisitos de "Base de Datos 2"')).toBeInTheDocument();
    expect(screen.getByText("0.42 s")).toBeInTheDocument();
  });

  it("never exposes the raw tool name, arguments, or result", () => {
    render(<ToolCallCard toolCall={toolCall} />);
    expect(screen.queryByText("get_prerequisites")).not.toBeInTheDocument();
    expect(screen.queryByText(/"course": "Base de Datos 2"/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Base de Datos 1/)).not.toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows an amber 0 filas pill instead of a duration when row_count is 0", () => {
    render(<ToolCallCard toolCall={{ ...toolCall, result: [], row_count: 0 }} />);
    expect(screen.getByText("0 filas")).toBeInTheDocument();
    expect(screen.queryByText("0.42 s")).not.toBeInTheDocument();
  });
});
