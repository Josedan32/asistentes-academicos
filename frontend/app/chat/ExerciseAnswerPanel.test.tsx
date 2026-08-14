import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ExerciseAnswerPanel } from "./ExerciseAnswerPanel";

describe("ExerciseAnswerPanel", () => {
  it("submits the typed answer and clears the input", async () => {
    const onSubmitAnswer = vi.fn();
    const user = userEvent.setup();
    render(<ExerciseAnswerPanel onSubmitAnswer={onSubmitAnswer} />);

    await user.type(screen.getByPlaceholderText(/tu respuesta/i), "mi respuesta");
    await user.click(screen.getByRole("button", { name: /enviar respuesta/i }));

    expect(onSubmitAnswer).toHaveBeenCalledWith("mi respuesta");
    expect(screen.getByPlaceholderText(/tu respuesta/i)).toHaveValue("");
  });

  it("does not submit an empty answer", async () => {
    const onSubmitAnswer = vi.fn();
    const user = userEvent.setup();
    render(<ExerciseAnswerPanel onSubmitAnswer={onSubmitAnswer} />);

    await user.click(screen.getByRole("button", { name: /enviar respuesta/i }));

    expect(onSubmitAnswer).not.toHaveBeenCalled();
  });
});
