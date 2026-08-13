import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CourseModal } from "./CourseModal";

const COURSE = {
  id: 1, code: "BD2", name: "Base de Datos 2", area: "Datos", default_credits: 4,
  placements: [],
};

function renderModal() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <CourseModal open course={COURSE} onClose={() => {}} onSubmit={() => {}} />
    </QueryClientProvider>
  );
}

describe("CourseModal — material de estudio", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/materials") && !url.match(/materials\/\d+$/)) {
        return Promise.resolve(
          new Response(JSON.stringify([{ id: 1, course_id: 1, filename: "guia.pdf" }]), {
            status: 200,
          })
        );
      }
      return Promise.resolve(new Response(JSON.stringify({}), { status: 200 }));
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("lists the course's existing material when editing", async () => {
    renderModal();
    expect(await screen.findByText("guia.pdf")).toBeInTheDocument();
  });
});
