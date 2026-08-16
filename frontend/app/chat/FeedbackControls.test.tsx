import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FeedbackControls } from "./FeedbackControls";

const message = {
  id: 42, clientId: "42", role: "assistant" as const, content: "respuesta", mode: null,
  toolCalls: [], feedback: null,
};

describe("FeedbackControls", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
      configurable: true,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("opens the comment card after clicking a thumb, without submitting yet", async () => {
    const user = userEvent.setup();
    render(<FeedbackControls message={message} onFeedbackSubmitted={() => {}} />);

    await user.click(screen.getByRole("button", { name: "Valorar positivamente" }));

    expect(screen.getByPlaceholderText(/no mencionó/i)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("Omitir submits the vote with no comment", async () => {
    const onFeedbackSubmitted = vi.fn();
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ id: 1 }), { status: 201 })
    );
    const user = userEvent.setup();
    render(<FeedbackControls message={message} onFeedbackSubmitted={onFeedbackSubmitted} />);

    await user.click(screen.getByRole("button", { name: "Valorar negativamente" }));
    await user.click(screen.getByRole("button", { name: /omitir/i }));

    await waitFor(() => expect(onFeedbackSubmitted).toHaveBeenCalledWith(42, {
      value: "down", comment: null,
    }));
    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(JSON.parse(options.body as string)).toEqual({ value: "down", comment: null });
  });

  it("Enviar comentario submits the vote with the typed comment", async () => {
    const onFeedbackSubmitted = vi.fn();
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ id: 2 }), { status: 201 })
    );
    const user = userEvent.setup();
    render(<FeedbackControls message={message} onFeedbackSubmitted={onFeedbackSubmitted} />);

    await user.click(screen.getByRole("button", { name: "Valorar positivamente" }));
    await user.type(screen.getByPlaceholderText(/no mencionó/i), "faltó horario");
    await user.click(screen.getByRole("button", { name: /enviar comentario/i }));

    await waitFor(() => expect(onFeedbackSubmitted).toHaveBeenCalledWith(42, {
      value: "up", comment: "faltó horario",
    }));
  });

  it("shows the already-recorded vote instead of the buttons once feedback exists", () => {
    render(
      <FeedbackControls
        message={{ ...message, feedback: { value: "up", comment: null } }}
        onFeedbackSubmitted={() => {}}
      />
    );
    expect(screen.queryByRole("button", { name: "Valorar positivamente" })).not.toBeInTheDocument();
    expect(screen.getByLabelText("Valoración positiva")).toBeInTheDocument();
  });
});
