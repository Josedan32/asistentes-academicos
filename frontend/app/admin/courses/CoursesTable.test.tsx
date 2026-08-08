import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CoursesTable } from "./CoursesTable";

function renderTable() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <CoursesTable />
    </QueryClientProvider>
  );
}

const COURSES = [
  {
    id: 1, code: "BDD-302", name: "Base de Datos 2", area: "Programación", default_credits: 3,
    placements: [
      { program_id: 1, program_code: "ISW", program_name: "Ing. Software", semester: 6, credits: 3 },
      { program_id: 2, program_code: "IEL", program_name: "Ing. Electrónica", semester: 5, credits: 3 },
    ],
  },
  {
    id: 2, code: "ARQ-520", name: "Arquitectura de Software", area: "Programación",
    default_credits: 4, placements: [],
  },
];

describe("CoursesTable", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(COURSES), { status: 200 })));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the program count for a shared course and 'Sin asignar' for an unused one", async () => {
    renderTable();
    expect(await screen.findByText("2 carreras")).toBeInTheDocument();
    expect(screen.getByText("Sin asignar")).toBeInTheDocument();
  });

  it("the area filter narrows the list", async () => {
    const user = userEvent.setup();
    renderTable();
    await screen.findByText("Base de Datos 2");

    await user.selectOptions(screen.getByLabelText(/área/i), "Programación");

    expect(screen.getByText("Base de Datos 2")).toBeInTheDocument();
  });

  it("the assignment filter isolates unassigned courses", async () => {
    const user = userEvent.setup();
    renderTable();
    await screen.findByText("Base de Datos 2");

    await user.selectOptions(screen.getByLabelText(/uso/i), "unassigned");

    expect(screen.queryByText("Base de Datos 2")).not.toBeInTheDocument();
    expect(screen.getByText("Arquitectura de Software")).toBeInTheDocument();
  });
});
