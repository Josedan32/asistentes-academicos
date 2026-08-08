import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { StatusBanner } from "./StatusBanner";

describe("StatusBanner", () => {
  it("renders nothing when idle or streaming", () => {
    const { container: idleContainer } = render(
      <StatusBanner runState="idle" queuedInfo={null} thinkingTool={null} errorInfo={null}
                    onStop={() => {}} onRetry={() => {}} />
    );
    expect(idleContainer).toBeEmptyDOMElement();

    const { container: streamingContainer } = render(
      <StatusBanner runState="streaming" queuedInfo={null} thinkingTool={null} errorInfo={null}
                    onStop={() => {}} onRetry={() => {}} />
    );
    expect(streamingContainer).toBeEmptyDOMElement();
  });

  it("shows the loading-model banner", () => {
    render(
      <StatusBanner runState="loading_model" queuedInfo={null} thinkingTool={null}
                    errorInfo={null} onStop={() => {}} onRetry={() => {}} />
    );
    expect(screen.getByText("Cargando el modelo en memoria")).toBeInTheDocument();
  });

  it("shows the thinking banner with the tool name and a working Detener button", async () => {
    const onStop = vi.fn();
    const user = userEvent.setup();
    render(
      <StatusBanner runState="thinking" queuedInfo={null} thinkingTool="get_prerequisites"
                    errorInfo={null} onStop={onStop} onRetry={() => {}} />
    );
    expect(screen.getByText("get_prerequisites")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /detener/i }));
    expect(onStop).toHaveBeenCalled();
  });

  it("shows the queued banner with position and a working Cancelar button", async () => {
    const onStop = vi.fn();
    const user = userEvent.setup();
    render(
      <StatusBanner runState="queued" queuedInfo={{ position: 2, estimatedWait: 20 }}
                    thinkingTool={null} errorInfo={null} onStop={onStop} onRetry={() => {}} />
    );
    expect(screen.getByText(/segundo lugar/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /cancelar/i }));
    expect(onStop).toHaveBeenCalled();
  });

  it("shows the error banner with a working Reintentar button", async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();
    render(
      <StatusBanner runState="error" queuedInfo={null} thinkingTool={null}
                    errorInfo={{ code: "agent_loop_failed", message: "boom" }}
                    onStop={() => {}} onRetry={onRetry} />
    );
    expect(screen.getByText(/no está disponible/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /reintentar/i }));
    expect(onRetry).toHaveBeenCalled();
  });
});
