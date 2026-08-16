import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ExerciseCard } from "./ExerciseCard";

const toolCall = {
  id: "1", name: "search_course_material", arguments: { query: "normalizacion" },
  result: { fragments: [{ text: "Un ejercicio real: normaliza esta tabla...", page: 4 }] },
  duration_ms: 120, row_count: 1,
};

describe("ExerciseCard", () => {
  it("shows the retrieved exercise text and an answer input", () => {
    render(<ExerciseCard toolCall={toolCall} onSubmitAnswer={() => {}} />);
    expect(screen.getByText(/normaliza esta tabla/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/tu respuesta/i)).toBeInTheDocument();
  });

  it("submits the typed answer and clears the input", async () => {
    const onSubmitAnswer = vi.fn();
    const user = userEvent.setup();
    render(<ExerciseCard toolCall={toolCall} onSubmitAnswer={onSubmitAnswer} />);

    await user.type(screen.getByPlaceholderText(/tu respuesta/i), "mi respuesta");
    await user.click(screen.getByRole("button", { name: /enviar respuesta/i }));

    expect(onSubmitAnswer).toHaveBeenCalledWith("mi respuesta");
    expect(screen.getByPlaceholderText(/tu respuesta/i)).toHaveValue("");
  });

  it("renders nothing when no fragments were found", () => {
    const { container } = render(
      <ExerciseCard
        toolCall={{ ...toolCall, result: { fragments: [] }, row_count: 0 }}
        onSubmitAnswer={() => {}}
      />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows a raw material fragment as plain text, not parsed as markdown/LaTeX", () => {
    const rawFragment = {
      ...toolCall,
      result: {
        fragments: [
          { text: "1 1 0\n0 1 0\n0 0 1\n**no es negrita** y $no es formula$", page: 62 },
        ],
      },
    };
    const { container } = render(<ExerciseCard toolCall={rawFragment} onSubmitAnswer={() => {}} />);

    expect(container.querySelector(".katex")).not.toBeInTheDocument();
    expect(container.querySelector("strong")).not.toBeInTheDocument();
    expect(container.textContent).toContain("**no es negrita**");
    expect(container.textContent).toContain("$no es formula$");
  });
});
