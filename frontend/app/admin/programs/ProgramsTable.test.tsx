import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ProgramsTable } from "./ProgramsTable";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

function renderTable() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ProgramsTable />
    </QueryClientProvider>
  );
}

const PROGRAM = {
  id: 1, code: "ISW", name: "Ingeniería en Software", semester_count: 10, is_active: true,
  course_count: 52,
};

describe("ProgramsTable", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, options?: RequestInit) => {
      const url = String(input);
      if (options?.method === "PATCH") {
        return Promise.resolve(
          new Response(JSON.stringify({ ...PROGRAM, name: "Ingeniería de Software" }), {
            status: 200,
          })
        );
      }
      return Promise.resolve(new Response(JSON.stringify([PROGRAM]), { status: 200 }));
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("lists programs with their course count and status badge", async () => {
    renderTable();
    const nameCell = await screen.findByText("Ingeniería en Software");
    const row = nameCell.closest("tr")!;
    expect(screen.getByText("52")).toBeInTheDocument();
    expect(within(row).getByText("Activa")).toBeInTheDocument();
  });

  it("filters by search text client-side", async () => {
    const user = userEvent.setup();
    renderTable();
    await screen.findByText("Ingeniería en Software");

    await user.type(screen.getByPlaceholderText(/buscar carrera/i), "Electrónica");

    expect(screen.queryByText("Ingeniería en Software")).not.toBeInTheDocument();
  });

  it("editing a program submits a PATCH and reflects the new name", async () => {
    const user = userEvent.setup();
    renderTable();
    await screen.findByText("Ingeniería en Software");

    await user.click(screen.getByRole("link", { name: /editar/i }));
    const nameInput = screen.getByDisplayValue("Ingeniería en Software");
    await user.clear(nameInput);
    await user.type(nameInput, "Ingeniería de Software");
    await user.click(screen.getByRole("button", { name: /guardar/i }));

    await waitFor(() => {
      const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls.find(
        ([, opts]) => opts?.method === "PATCH"
      )!;
      expect(JSON.parse(options!.body as string).name).toBe("Ingeniería de Software");
    });
  });
});
