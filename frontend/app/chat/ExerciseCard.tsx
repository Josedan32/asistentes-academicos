"use client";

import { useState } from "react";
import type { ChatToolCall } from "@/lib/hooks/useChatStream";

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
  const fragments = (toolCall.result as { fragments: MaterialFragment[] } | undefined)
    ?.fragments ?? [];

  if (fragments.length === 0) {
    return (
      <div className="rounded-card-lg border border-amber-border bg-amber-bg p-[14px] text-[14px]
                       text-amber-text">
        No encontré un ejercicio de eso en el material de la materia.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 rounded-card-lg border border-tool-border bg-tool-bg
                     p-[14px]">
      <div className="text-[10.5px] font-semibold uppercase tracking-[.14em] text-text-tertiary">
        Ejercicio del material del curso
      </div>
      {fragments.map((fragment, index) => (
        <p key={index} className="m-0 text-[14.5px] leading-[1.6] text-text-body">
          {fragment.text}
        </p>
      ))}
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
          }}
          className="h-10 flex-none rounded-control bg-navy px-4 text-[13px] font-semibold
                     text-white"
        >
          Enviar respuesta
        </button>
      </div>
    </div>
  );
}
