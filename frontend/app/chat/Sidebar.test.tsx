import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Sidebar } from "./Sidebar";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200 });
}

function renderSidebar(props: Partial<React.ComponentProps<typeof Sidebar>> = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const onClose = vi.fn();
  render(
    <QueryClientProvider client={client}>
      <Sidebar
        activeAssistant={{ type: "general" }}
        onSelectAssistant={vi.fn()}
        onNewConversation={vi.fn()}
        activeConversationId={null}
        onSelectConversation={vi.fn()}
        isOpen={false}
        onClose={onClose}
        {...props}
      />
    </QueryClientProvider>
  );
  return { onClose };
}

describe("Sidebar", () => {
  beforeEach(() => {
    localStorage.setItem("pb_token", "tok");
    localStorage.setItem("pb_role", "student");
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/v1/me")) {
        return Promise.resolve(jsonResponse({
          id: 1, email: "ana@pascualbravo.edu.co", role: "student", first_name: "Ana",
          last_name: "Marin", document: "1", program_id: 1, program_code: "ISW",
          program_name: "Ingeniería en Software", current_semester: 5,
        }));
      }
      if (url.endsWith("/api/v1/me/enrollments")) return Promise.resolve(jsonResponse([]));
      if (url.endsWith("/api/v1/chat/conversations")) return Promise.resolve(jsonResponse([]));
      return Promise.resolve(jsonResponse({}));
    }));
  });

  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("shows no backdrop when closed", () => {
    renderSidebar({ isOpen: false });
    expect(document.querySelector(".bg-black\\/50")).not.toBeInTheDocument();
  });

  it("clicking the backdrop closes the sidebar", async () => {
    const user = userEvent.setup();
    const { onClose } = renderSidebar({ isOpen: true });

    const backdrop = document.querySelector(".bg-black\\/50");
    expect(backdrop).toBeInTheDocument();
    await user.click(backdrop as Element);

    expect(onClose).toHaveBeenCalled();
  });

  it("selecting an assistant closes the mobile drawer", async () => {
    const user = userEvent.setup();
    const onSelectAssistant = vi.fn();
    const { onClose } = renderSidebar({ isOpen: true, onSelectAssistant });

    await user.click(await screen.findByText("General de Carrera"));

    expect(onSelectAssistant).toHaveBeenCalledWith({ type: "general" });
    expect(onClose).toHaveBeenCalled();
  });

  it("starting a new conversation closes the mobile drawer", async () => {
    const user = userEvent.setup();
    const onNewConversation = vi.fn();
    const { onClose } = renderSidebar({ isOpen: true, onNewConversation });

    await user.click(screen.getByText("+ Nueva conversación"));

    expect(onNewConversation).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });
});
