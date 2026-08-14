"use client";

import { useRef, useState } from "react";
import { ArrowUp, Paperclip, Square, X } from "lucide-react";
import { uploadChatAttachment } from "@/lib/api/chat-attachments";
import type { RunState } from "@/lib/hooks/useChatStream";

const BUSY_STATES: RunState[] = ["loading_model", "thinking", "queued", "streaming"];

interface Attachment {
  filename: string;
  text: string;
}

export function Composer({
  runState, onSend, onStop, modeSelector,
}: {
  runState: RunState;
  onSend: (text: string) => void;
  onStop: () => void;
  modeSelector?: React.ReactNode;
}) {
  const [value, setValue] = useState("");
  const [attachment, setAttachment] = useState<Attachment | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const busy = BUSY_STATES.includes(runState);
  const offline = runState === "error";

  const placeholder = busy
    ? "Espera a que termine la respuesta actual…"
    : offline
      ? "El asistente no está disponible"
      : "Escribe tu pregunta sobre la carrera…";

  function submit() {
    const text = value.trim();
    if (!text || busy || offline) return;
    const outgoing = attachment
      ? `Archivo adjunto "${attachment.filename}":\n${attachment.text}\n\n---\n\n${text}`
      : text;
    onSend(outgoing);
    setValue("");
    setAttachment(null);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  async function handleFileSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setUploadError(null);
    setUploading(true);
    try {
      const result = await uploadChatAttachment(file);
      setAttachment({ filename: result.filename, text: result.text });
    } catch {
      setUploadError("No se pudo leer el archivo. Usa PDF o Word.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {(attachment || uploading || uploadError) && (
        <div className="flex items-center gap-2 rounded-control border border-border-control
                         bg-app-bg px-[10px] py-[6px] text-[12.5px] text-text-secondary">
          <Paperclip className="h-3 w-3 flex-none" />
          {uploading && <span>Leyendo archivo…</span>}
          {!uploading && uploadError && <span className="text-error-text">{uploadError}</span>}
          {!uploading && !uploadError && attachment && (
            <>
              <span className="truncate">{attachment.filename}</span>
              <button
                onClick={() => setAttachment(null)}
                aria-label="Quitar archivo adjunto"
                className="ml-auto text-text-tertiary hover:text-navy"
              >
                <X className="h-3 w-3" />
              </button>
            </>
          )}
        </div>
      )}

      <div className="flex items-end gap-3 rounded-container border border-border-control
                       bg-surface p-[12px_14px]">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileSelected}
          className="hidden"
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={busy || offline || uploading}
          aria-label="Adjuntar archivo"
          title="Adjuntar un PDF o Word a esta conversación"
          className="flex h-10 w-10 flex-none items-center justify-center rounded-[9px] border
                     border-border-control bg-app-bg text-text-secondary hover:bg-surface
                     disabled:opacity-50"
        >
          <Paperclip className="h-[16px] w-[16px]" />
        </button>
        {modeSelector}
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={busy || offline}
          placeholder={placeholder}
          className="max-h-[120px] min-h-[26px] flex-1 resize-none border-none bg-transparent
                     text-[15.5px] leading-[1.5] text-navy outline-none disabled:opacity-60"
        />
        {busy ? (
          <button
            onClick={onStop}
            aria-label="Detener respuesta"
            className="flex h-10 w-10 flex-none items-center justify-center rounded-[9px]
                       bg-error-accent text-[13px] text-white"
          >
            <Square className="h-[15px] w-[15px] fill-current" />
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={offline || value.trim() === ""}
            className="flex h-10 w-10 flex-none items-center justify-center rounded-[9px]
                       bg-navy text-white disabled:bg-[#C2CAD4]"
          >
            <ArrowUp className="h-[15px] w-[15px]" />
          </button>
        )}
      </div>
      <div className="text-center text-[12px] text-text-tertiary">
        El asistente responde con datos de la malla registrada por coordinación. Verifica
        siempre con Registro Académico antes de matricular.
      </div>
    </div>
  );
}
