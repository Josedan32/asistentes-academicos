import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AssignCoursePanel } from "./AssignCoursePanel";

const PROGRAM = { id: 1, code: "ISW", name: "Ingeniería en Software", semester_count: 10, is_active: true, course_count: 52 };
const CATALOG = [
  {
    id: 10, code: "BDD-302", name: "Base de Datos 2", area: "Programación", default_credits: 3,
    placements: [{ program_id: 2, program_code: "IEL", program_name: "Ing. Electrónica", semester: 5, credits: 3 }],
  },
  {
    id: 11, code: "BDD-301", name: "Base de Datos 1", area: "Programación", default_credits: 3,
    placements: [{ program_id: 1, program_code: "ISW", program_name: "Ing. Software", semester: 4, credits: 3 }],
  },
];

function renderPanel() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <AssignCoursePanel open program={PROGRAM} targetSemester={6} earlierSemesterCourses={[]}
                          onClose={() => {}} />
    </QueryClientProvider>
  );
}

describe("AssignCoursePanel", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, options?: RequestInit) => {
      const url = String(input);
      if (options?.method === "POST" && url.endsWith("/curriculum")) {
        return Promise.resolve(new Response(JSON.stringify({}), { status: 201 }));
      }
      return Promise.resolve(new Response(JSON.stringify(CATALOG), { status: 200 }));
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the shared-course amber warning for a course used in another program", async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.type(screen.getByPlaceholderText(/nombre o código/i), "base de datos");

    expect(await screen.findByText("Ya existe")).toBeInTheDocument();
    expect(screen.getByText(/también está en/i)).toBeInTheDocument();
    expect(screen.getByText(/Ing\. Electrónica, semestre 5/)).toBeInTheDocument();
  });

  it("shows a plain 'Ya en semestre N' row for a course already in this program", async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.type(screen.getByPlaceholderText(/nombre o código/i), "base de datos 1");

    expect(await screen.findByText("Ya en semestre 4")).toBeInTheDocument();
  });

  it("selecting a shared match and submitting assigns it with the chosen semester and credits", async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.type(screen.getByPlaceholderText(/nombre o código/i), "base de datos 2");
    await user.click(await screen.findByText("Base de Datos 2"));
    await user.click(screen.getByRole("button", { name: /asignar a semestre/i }));

    await waitFor(() => {
      const call = (fetch as ReturnType<typeof vi.fn>).mock.calls.find(
        ([, opts]) => opts?.method === "POST"
      );
      expect(call).toBeDefined();
      const body = JSON.parse(call![1]!.body as string);
      expect(body).toMatchObject({ course_id: 10, semester: 6, credits: 3 });
    });
  });
});
