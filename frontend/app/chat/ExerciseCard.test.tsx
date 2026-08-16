import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ExerciseCard } from "./ExerciseCard";

const toolCall = {
  id: "1", name: "search_course_material", arguments: { query: "normalizacion" },
  result: { fragments: [{ text: "Un ejercicio real: normaliza esta tabla...", page: 4 }] },
  duration_ms: 120, row_count: 1,
};

describe("ExerciseCard", () => {
  it("shows the source citation with the page number, not the raw fragment text", () => {
    render(<ExerciseCard toolCall={toolCall} />);
    expect(screen.getByText("Ejercicio del material del curso")).toBeInTheDocument();
    expect(screen.getByText("pág. 4")).toBeInTheDocument();
    expect(screen.queryByText(/normaliza esta tabla/)).not.toBeInTheDocument();
  });

  it("omits the page badge when the fragment has no page", () => {
    const noPage = { ...toolCall, result: { fragments: [{ text: "x", page: null }] } };
    render(<ExerciseCard toolCall={noPage} />);
    expect(screen.queryByText(/pág\./)).not.toBeInTheDocument();
  });

  it("renders nothing when no fragments were found", () => {
    const { container } = render(
      <ExerciseCard toolCall={{ ...toolCall, result: { fragments: [] }, row_count: 0 }} />
    );
    expect(container).toBeEmptyDOMElement();
  });
});
