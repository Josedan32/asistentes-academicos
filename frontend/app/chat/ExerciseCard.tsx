"use client";

import { useState } from "react";
import { Eraser, PenLine, SearchX, Send } from "lucide-react";
import type { ChatToolCall } from "@/lib/hooks/useChatStream";
import { MarkdownContent } from "./MarkdownContent";

interface MaterialFragment {
  text: string;
  page: number | null;
}

export function ExerciseCard({
  toolCall, onSubmitAnswer,
}: {
  toolCall: ChatToolCall;
  onSubmitAnswer: (answer: string) => void;
}) {
  const [answer, setAnswer] = useState("");
  const [scratch, setScratch] = useState("");
  const fragments = (toolCall.result as { fragments: MaterialFragment[] } | undefined)
    ?.fragments ?? [];

  if (fragments.length === 0) {
    return (
      <div className="flex items-center gap-[10px] rounded-card-lg border border-amber-border
                       bg-amber-bg p-[14px] text-[14px] text-amber-text">
        <SearchX className="h-[18px] w-[18px] flex-none text-amber-accent" />
        No encontré un ejercicio de eso en el material de la materia — sigo abajo con uno
        propio.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 overflow-hidden rounded-card-lg border
                     border-tool-border bg-tool-bg">
      <div className="flex items-center gap-2 border-b border-tool-border-inner bg-accent
                       px-[14px] py-[10px]">
        <PenLine className="h-[14px] w-[14px] flex-none text-white" />
        <span className="text-[11px] font-semibold uppercase tracking-[.14em] text-white">
          Ejercicio del material del curso
        </span>
        {fragments[0]?.page != null && (
          <span className="ml-auto rounded-pill bg-white/15 px-[9px] py-[2px] text-[11.5px]
                            text-white">
            pág. {fragments[0].page}
          </span>
        )}
      </div>

      <div className="flex flex-col gap-3 px-[14px] pb-[14px]">
        {fragments.map((fragment, index) => (
          <div key={index} className="text-[14.5px] leading-[1.6] text-text-body">
            <MarkdownContent content={fragment.text} />
          </div>
        ))}

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
            className="min-h-20 resize-y rounded-control border border-dashed
                       border-border-control bg-surface p-[10px_12px] font-mono text-[13.5px]
                       leading-[1.5] text-navy outline-none focus-visible:border-accent"
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
    </div>
  );
}
