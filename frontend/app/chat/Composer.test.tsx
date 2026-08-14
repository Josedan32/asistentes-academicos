import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Composer } from "./Composer";
import { uploadChatAttachment } from "@/lib/api/chat-attachments";

vi.mock("@/lib/api/chat-attachments", () => ({
  uploadChatAttachment: vi.fn(),
}));

describe("Composer", () => {
  it("sends on Enter and clears the input", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();
    render(<Composer runState="idle" onSend={onSend} onStop={() => {}} />);

    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, "hola{Enter}");

    expect(onSend).toHaveBeenCalledWith("hola");
    expect(textarea).toHaveValue("");
  });

  it("inserts a newline on Shift+Enter instead of sending", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();
    render(<Composer runState="idle" onSend={onSend} onStop={() => {}} />);

    const textarea = screen.getByPlaceholderText(/escribe tu pregunta/i);
    await user.type(textarea, "linea1{Shift>}{Enter}{/Shift}linea2");

    expect(onSend).not.toHaveBeenCalled();
    expect(textarea).toHaveValue("linea1\nlinea2");
  });

  it("disables the textarea and shows a stop button while busy", () => {
    render(<Composer runState="thinking" onSend={() => {}} onStop={() => {}} />);
    expect(screen.getByPlaceholderText(/espera a que termine/i)).toBeDisabled();
    expect(screen.getByRole("button", { name: "Detener respuesta" })).toBeInTheDocument();
  });

  it("clicking the stop button while busy calls onStop", async () => {
    const onStop = vi.fn();
    const user = userEvent.setup();
    render(<Composer runState="streaming" onSend={() => {}} onStop={onStop} />);

    await user.click(screen.getByRole("button", { name: "Detener respuesta" }));

    expect(onStop).toHaveBeenCalled();
  });

  it("disables the textarea when offline (error state)", () => {
    render(<Composer runState="error" onSend={() => {}} onStop={() => {}} />);
    expect(screen.getByPlaceholderText(/no está disponible/i)).toBeDisabled();
  });

  it("attaches a file and folds its text into the outgoing message", async () => {
    vi.mocked(uploadChatAttachment).mockResolvedValue({
      filename: "apuntes.pdf", text: "contenido del pdf",
    });
    const onSend = vi.fn();
    const user = userEvent.setup();
    render(<Composer runState="idle" onSend={onSend} onStop={() => {}} />);

    const file = new File(["contenido"], "apuntes.pdf", { type: "application/pdf" });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(fileInput, file);

    expect(await screen.findByText("apuntes.pdf")).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText(/escribe tu pregunta/i), "explícame esto{Enter}");

    expect(onSend).toHaveBeenCalledWith(
      'Archivo adjunto "apuntes.pdf":\ncontenido del pdf\n\n---\n\nexplícame esto'
    );
    expect(screen.queryByText("apuntes.pdf")).not.toBeInTheDocument();
  });

  it("shows an error and no chip when the upload fails", async () => {
    vi.mocked(uploadChatAttachment).mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    render(<Composer runState="idle" onSend={() => {}} onStop={() => {}} />);

    const file = new File(["contenido"], "notas.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(fileInput, file);

    expect(await screen.findByText(/no se pudo leer el archivo/i)).toBeInTheDocument();
  });
});
