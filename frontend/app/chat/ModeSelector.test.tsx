import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ModeSelector } from "./ModeSelector";

describe("ModeSelector", () => {
  it("opens the dropdown and calls onModeChange when a mode is picked", async () => {
    const onModeChange = vi.fn();
    const user = userEvent.setup();
    render(<ModeSelector mode="consulta" onModeChange={onModeChange} disabled={false} />);

    await user.click(screen.getByRole("button", { name: /modo del asistente/i }));
    await user.click(await screen.findByRole("menuitem", { name: /práctica/i }));

    expect(onModeChange).toHaveBeenCalledWith("practica");
  });

  it("labels the trigger with the active mode", () => {
    render(<ModeSelector mode="examen" onModeChange={() => {}} disabled={false} />);
    expect(
      screen.getByRole("button", { name: /modo del asistente: examen/i })
    ).toBeInTheDocument();
  });

  it("disables the trigger while busy", () => {
    render(<ModeSelector mode="consulta" onModeChange={() => {}} disabled />);
    expect(screen.getByRole("button", { name: /modo del asistente/i })).toBeDisabled();
  });
});
