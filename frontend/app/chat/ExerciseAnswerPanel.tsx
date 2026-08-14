"use client";

import { useState } from "react";
import { Eraser, Send } from "lucide-react";

export function ExerciseAnswerPanel({ onSubmitAnswer }: { onSubmitAnswer: (answer: string) => void }) {
  const [answer, setAnswer] = useState("");
  const [scratch, setScratch] = useState("");

  return (
    <div className="flex flex-col gap-3 rounded-card-lg border border-tool-border bg-tool-bg
                     p-[14px]">
      <div className="flex flex-col gap-[6px]">
        <div className="flex items-center justify-between">
          <span className="text-[10.5px] font-semibold uppercase tracking-[.14em]
                            text-text-tertiary">
            Tablero para calcular (borrador, no se envía)
          </span>
          {scratch !== "" && (
            <button
              onClick={() => setScratch("")}
              aria-label="Borrar tablero"
              className="flex items-center gap-1 text-[12px] font-medium text-text-tertiary
                         hover:text-navy"
            >
              <Eraser className="h-3 w-3" /> Borrar
            </button>
          )}
        </div>
        <textarea
          value={scratch}
          onChange={(event) => setScratch(event.target.value)}
          placeholder="Usa este espacio para hacer tus cálculos antes de responder…"
          className="min-h-20 resize-y rounded-control border border-dashed border-border-control
                     bg-surface p-[10px_12px] font-mono text-[13.5px] leading-[1.5] text-navy
                     outline-none focus-visible:border-accent"
        />
      </div>

      <div className="flex items-end gap-2">
        <textarea
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          placeholder="Tu respuesta..."
          className="min-h-16 flex-1 resize-y rounded-control border border-border-control
                     bg-surface p-[10px_12px] text-[14px] leading-[1.5] text-navy outline-none
                     focus-visible:border-accent"
        />
        <button
          onClick={() => {
            if (!answer.trim()) return;
            onSubmitAnswer(answer.trim());
            setAnswer("");
            setScratch("");
          }}
          className="flex h-10 flex-none items-center gap-[6px] rounded-control bg-navy
                     px-4 text-[13px] font-semibold text-white hover:bg-navy-hover"
        >
          <Send className="h-[13px] w-[13px]" />
          Enviar respuesta
        </button>
      </div>
    </div>
  );
}
