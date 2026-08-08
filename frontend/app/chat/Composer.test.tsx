import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Composer } from "./Composer";

describe("Composer", () => {
  it("sends on Enter and clears the input", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();
    render(<Composer runState="idle" onSend={onSend} onStop={() => {}} />);

    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, "hola{Enter}");

    expect(onSend).toHaveBeenCalledWith("hola");
    expect(textarea).toHaveValue("");
  });

  it("inserts a newline on Shift+Enter instead of sending", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();
    render(<Composer runState="idle" onSend={onSend} onStop={() => {}} />);

    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, "linea1{Shift>}{Enter}{/Shift}linea2");

    expect(onSend).not.toHaveBeenCalled();
    expect(textarea).toHaveValue("linea1\nlinea2");
  });

  it("disables the textarea and shows a stop button while busy", () => {
    render(<Composer runState="thinking" onSend={() => {}} onStop={() => {}} />);
    expect(screen.getByPlaceholderText(/espera a que termine/i)).toBeDisabled();
    expect(screen.getByRole("button")).toHaveTextContent("■");
  });

  it("clicking the stop button while busy calls onStop", async () => {
    const onStop = vi.fn();
    const user = userEvent.setup();
    render(<Composer runState="streaming" onSend={() => {}} onStop={onStop} />);

    await user.click(screen.getByRole("button"));

    expect(onStop).toHaveBeenCalled();
  });

  it("disables the textarea when offline (error state)", () => {
    render(<Composer runState="error" onSend={() => {}} onStop={() => {}} />);
    expect(screen.getByPlaceholderText(/no está disponible/i)).toBeDisabled();
  });
});
