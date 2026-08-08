"use client";

import { useState } from "react";
import { ArrowUp } from "lucide-react";
import type { RunState } from "@/lib/hooks/useChatStream";

const BUSY_STATES: RunState[] = ["loading_model", "thinking", "queued", "streaming"];

export function Composer({
  runState, onSend, onStop,
}: {
  runState: RunState;
  onSend: (text: string) => void;
  onStop: () => void;
}) {
  const [value, setValue] = useState("");
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
    onSend(text);
    setValue("");
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-end gap-3 rounded-container border border-border-control
                       bg-surface p-[12px_14px]">
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
            className="flex h-10 w-10 flex-none items-center justify-center rounded-[9px]
                       bg-error-accent text-[13px] text-white"
          >
            ■
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
