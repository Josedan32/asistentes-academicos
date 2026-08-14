"use client";

import { useRef, useState } from "react";
import { Send } from "lucide-react";
import { ScratchCanvas, type ScratchCanvasHandle } from "./ScratchCanvas";

export function ExerciseAnswerPanel({ onSubmitAnswer }: { onSubmitAnswer: (answer: string) => void }) {
  const [answer, setAnswer] = useState("");
  const scratchRef = useRef<ScratchCanvasHandle>(null);

  return (
    <div className="flex flex-col gap-3 rounded-card-lg border border-tool-border bg-tool-bg
                     p-[14px]">
      <ScratchCanvas ref={scratchRef} />

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
            scratchRef.current?.clear();
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
