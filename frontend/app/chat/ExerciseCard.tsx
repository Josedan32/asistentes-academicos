"use client";

import { PenLine } from "lucide-react";
import type { ChatToolCall } from "@/lib/hooks/useChatStream";

interface MaterialFragment {
  text: string;
  page: number | null;
}

export function ExerciseCard({ toolCall }: { toolCall: ChatToolCall }) {
  const fragments = (toolCall.result as { fragments: MaterialFragment[] } | undefined)
    ?.fragments ?? [];

  if (fragments.length === 0) return null;

  return (
    <div className="flex items-center gap-2 overflow-hidden rounded-card-lg border
                     border-tool-border bg-accent px-[14px] py-[10px]">
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
  );
}
