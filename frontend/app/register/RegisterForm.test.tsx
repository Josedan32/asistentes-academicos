import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { RegisterForm } from "./RegisterForm";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

function renderWithQueryClient() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <RegisterForm />
    </QueryClientProvider>
  );
}

describe("RegisterForm", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("recomputes the assistant preview when program and semester change", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockImplementation((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/programs") && !url.includes("curriculum")) {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              { id: 1, code: "ISW", name: "Ingeniería en Software", semester_count: 10,
                is_active: true, course_count: 52 },
            ]),
            { status: 200 }
          )
        );
      }
      if (url.includes("/curriculum?semester=5")) {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              { id: 10, code: "BDD-302", name: "Base de Datos 2", area: "Datos", credits: 3,
                semester: 5 },
            ]),
            { status: 200 }
          )
        );
      }
      return Promise.resolve(new Response(JSON.stringify([]), { status: 200 }));
    });

    const user = userEvent.setup();
    renderWithQueryClient();

    await screen.findByText("Ingeniería en Software");
    await user.selectOptions(screen.getByLabelText(/carrera/i), "1");
    await user.click(screen.getByRole("button", { name: "5" }));

    await waitFor(() => {
      expect(screen.getByText(/tendrás asistentes para Base de Datos 2/)).toBeInTheDocument();
    });
  });
});
