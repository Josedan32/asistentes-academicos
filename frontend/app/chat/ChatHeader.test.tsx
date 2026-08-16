import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ChatHeader } from "./ChatHeader";
import type { ActiveAssistant } from "@/lib/assistant-identity";

function renderHeader(
  activeAssistant: ActiveAssistant,
  mode?: "consulta" | "practica",
  onOpenSidebar?: () => void
) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ChatHeader activeAssistant={activeAssistant} mode={mode} onOpenSidebar={onOpenSidebar} />
    </QueryClientProvider>
  );
}

describe("ChatHeader", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 200 })));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("always shows the current mode as visible text, not only inside the selector", () => {
    renderHeader({ type: "course", courseId: 1, courseName: "Algebra Lineal" }, "practica");
    expect(screen.getByText("Modo actual del asistente:")).toBeInTheDocument();
    expect(screen.getByText("Práctica")).toBeInTheDocument();
  });

  it("hides the mode label for the general assistant, matching the mode selector's own scope", () => {
    renderHeader({ type: "general" }, "consulta");
    expect(screen.queryByText("Modo actual del asistente:")).not.toBeInTheDocument();
  });

  it("the mobile menu button opens the sidebar", async () => {
    const user = userEvent.setup();
    const onOpenSidebar = vi.fn();
    renderHeader({ type: "general" }, "consulta", onOpenSidebar);

    await user.click(screen.getByLabelText("Abrir menú"));

    expect(onOpenSidebar).toHaveBeenCalled();
  });
});
