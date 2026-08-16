"use client";

import { PenLine } from "lucide-react";
import type { ChatToolCall } from "@/lib/hooks/useChatStream";
import { ExerciseAnswerPanel } from "./ExerciseAnswerPanel";

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
  const fragments = (toolCall.result as { fragments: MaterialFragment[] } | undefined)
    ?.fragments ?? [];

  if (fragments.length === 0) return null;

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
          <div
            key={index}
            className="whitespace-pre-wrap text-[14.5px] leading-[1.6] text-text-body"
          >
            {fragment.text}
          </div>
        ))}
        <ExerciseAnswerPanel onSubmitAnswer={onSubmitAnswer} />
      </div>
    </div>
  );
}
