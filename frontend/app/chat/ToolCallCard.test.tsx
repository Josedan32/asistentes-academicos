import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { ToolCallCard } from "./ToolCallCard";

const toolCall = {
  id: "1", name: "get_prerequisites", arguments: { course: "Base de Datos 2" },
  result: { prerequisites: [{ course_name: "Base de Datos 1" }] },
  duration_ms: 420, row_count: 1,
};

describe("ToolCallCard", () => {
  it("shows the Spanish description and duration collapsed by default", () => {
    render(<ToolCallCard toolCall={toolCall} defaultOpen={false} />);
    expect(screen.getByText('Consultando prerrequisitos de "Base de Datos 2"')).toBeInTheDocument();
    expect(screen.getByText("0.42 s")).toBeInTheDocument();
    expect(screen.queryByText("get_prerequisites")).not.toBeInTheDocument();
  });

  it("reveals the tool name, arguments, and result on click", async () => {
    const user = userEvent.setup();
    render(<ToolCallCard toolCall={toolCall} defaultOpen={false} />);

    await user.click(screen.getByText(/ver detalle/i));

    expect(screen.getByText("get_prerequisites")).toBeInTheDocument();
    expect(screen.getByText(/"course": "Base de Datos 2"/)).toBeInTheDocument();
    expect(screen.getByText(/Base de Datos 1/)).toBeInTheDocument();
  });

  it("shows an amber 0 filas pill instead of a duration when row_count is 0", () => {
    render(
      <ToolCallCard
        toolCall={{ ...toolCall, result: [], row_count: 0 }}
        defaultOpen={false}
      />
    );
    expect(screen.getByText("0 filas")).toBeInTheDocument();
    expect(screen.queryByText("0.42 s")).not.toBeInTheDocument();
  });
});
