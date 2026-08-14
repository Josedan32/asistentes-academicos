import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { setSessionAssistant, setSessionMode } from "@/lib/chat-session-state";
import { ChatShell } from "./ChatShell";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

function renderShell() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ChatShell />
    </QueryClientProvider>
  );
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

describe("ChatShell", () => {
  beforeEach(() => {
    setSessionMode("consulta");
    setSessionAssistant({ type: "general" });
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
      if (url.includes("/api/v1/chat/model")) return Promise.resolve(jsonResponse({ model: "qwen2.5:3b" }));
      if (url.endsWith("/api/v1/me/enrollments")) return Promise.resolve(jsonResponse([]));
      if (url.endsWith("/api/v1/chat/conversations")) return Promise.resolve(jsonResponse([]));
      return Promise.resolve(jsonResponse({}));
    }));
  });

  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("shows the empty state with the student's name for a fresh conversation", async () => {
    renderShell();
    expect(await screen.findByText("Hola, Ana.")).toBeInTheDocument();
  });

  it("clicking a suggested question sends it immediately", async () => {
    const user = userEvent.setup();
    (fetch as ReturnType<typeof vi.fn>).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/v1/chat")) {
        const body = new ReadableStream<Uint8Array>({
          start(controller) {
            controller.enqueue(new TextEncoder().encode(
              'event: token\ndata: {"text":"Respuesta."}\n\n' +
              'event: done\ndata: {"tool_count":0,"total_ms":0,"source_count":0,' +
              '"conversation_id":1,"message_id":1}\n\n'
            ));
            controller.close();
          },
        });
        return Promise.resolve(new Response(body, { status: 200 }));
      }
      if (url.endsWith("/api/v1/me")) {
        return Promise.resolve(jsonResponse({
          id: 1, email: "ana@pascualbravo.edu.co", role: "student", first_name: "Ana",
          last_name: "Marin", document: "1", program_id: 1, program_code: "ISW",
          program_name: "Ingeniería en Software", current_semester: 5,
        }));
      }
      if (url.includes("/api/v1/chat/model")) return Promise.resolve(jsonResponse({ model: "qwen2.5:3b" }));
      if (url.endsWith("/api/v1/me/enrollments")) return Promise.resolve(jsonResponse([]));
      if (url.endsWith("/api/v1/chat/conversations")) return Promise.resolve(jsonResponse([]));
      return Promise.resolve(jsonResponse({}));
    });
    renderShell();
    const suggestion = await screen.findByText(/qué materias puedo matricular en semestre 6/i);

    await user.click(suggestion);

    await waitFor(() => expect(screen.getByText("Respuesta.")).toBeInTheDocument());
  });
});
