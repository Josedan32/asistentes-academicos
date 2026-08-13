import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ModeSelector } from "./ModeSelector";

describe("ModeSelector", () => {
  it("shows all five modes and calls onModeChange when one is picked", async () => {
    const onModeChange = vi.fn();
    const user = userEvent.setup();
    render(<ModeSelector mode="consulta" onModeChange={onModeChange} disabled={false} />);

    await user.click(screen.getByRole("button", { name: /práctica/i }));

    expect(onModeChange).toHaveBeenCalledWith("practica");
  });

  it("disables every button while busy", () => {
    render(<ModeSelector mode="consulta" onModeChange={() => {}} disabled />);
    for (const button of screen.getAllByRole("button")) {
      expect(button).toBeDisabled();
    }
  });
});
