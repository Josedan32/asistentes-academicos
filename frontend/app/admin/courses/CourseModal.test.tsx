import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

  it("shows an error and keeps the list intact when upload fails", async () => {
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST") {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "Unsupported format" }), { status: 422 })
        );
      }
      if (url.includes("/materials") && !url.match(/materials\/\d+$/)) {
        return Promise.resolve(
          new Response(JSON.stringify([{ id: 1, course_id: 1, filename: "guia.pdf" }]), {
            status: 200,
          })
        );
      }
      return Promise.resolve(new Response(JSON.stringify({}), { status: 200 }));
    }));

    const user = userEvent.setup();
    renderModal();
    await screen.findByText("guia.pdf");

    const file = new File(["dummy"], "material.pdf", { type: "application/pdf" });
    await user.upload(screen.getByLabelText(/subir pdf o word/i), file);

    expect(
      await screen.findByText("No se pudo subir el archivo. Verifica el formato (solo PDF o Word).")
    ).toBeInTheDocument();
    expect(screen.getByText("guia.pdf")).toBeInTheDocument();
  });

  it("shows a processing indicator while the upload request is in flight", async () => {
    let resolveUpload: (response: Response) => void = () => {};
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === "POST") {
        return new Promise<Response>((resolve) => {
          resolveUpload = resolve;
        });
      }
      if (url.includes("/materials") && !url.match(/materials\/\d+$/)) {
        return Promise.resolve(
          new Response(JSON.stringify([{ id: 1, course_id: 1, filename: "guia.pdf" }]), {
            status: 200,
          })
        );
      }
      return Promise.resolve(new Response(JSON.stringify({}), { status: 200 }));
    }));

    const user = userEvent.setup();
    renderModal();
    await screen.findByText("guia.pdf");

    const file = new File(["dummy"], "material.pdf", { type: "application/pdf" });
    await user.upload(screen.getByLabelText(/subir pdf o word/i), file);

    expect(await screen.findByText(/subiendo y procesando el material/i)).toBeInTheDocument();

    resolveUpload(new Response(JSON.stringify({ id: 2, course_id: 1, filename: "material.pdf" }), {
      status: 201,
    }));

    await waitFor(() => {
      expect(screen.queryByText(/subiendo y procesando el material/i)).not.toBeInTheDocument();
    });
  });
});
