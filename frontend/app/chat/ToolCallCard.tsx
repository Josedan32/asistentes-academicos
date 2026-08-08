"use client";

import { useState } from "react";
import { Settings2 } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { describeToolCall } from "@/lib/describe-tool-call";
import type { ChatToolCall } from "@/lib/hooks/useChatStream";

export function ToolCallCard({
  toolCall, defaultOpen,
}: {
  toolCall: ChatToolCall;
  defaultOpen: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const description = describeToolCall(toolCall.name, toolCall.arguments);
  const hasNoRows = toolCall.row_count === 0;

  return (
    <Collapsible open={open} onOpenChange={setOpen}
                 className="overflow-hidden rounded-card-lg border border-tool-border bg-tool-bg">
      <CollapsibleTrigger asChild>
        <div className="flex cursor-pointer items-center gap-[10px] px-[14px] py-[11px]">
          <Settings2 className="h-[13px] w-[13px] flex-none text-accent" />
          <span className="min-w-0 flex-1 truncate font-mono text-[13.5px] font-medium
                            text-tool-text">
            {description}
          </span>
          {hasNoRows ? (
            <span className="rounded-pill bg-amber-chip-bg px-[9px] py-[2px] text-[12px]
                              font-medium text-amber-text-muted">
              0 filas
            </span>
          ) : (
            <span className="rounded-pill bg-tool-pill-bg px-[9px] py-[2px] text-[12px]
                              text-accent-faint">
              {(toolCall.duration_ms / 1000).toFixed(2)} s
            </span>
          )}
          <span className="text-[12.5px] font-medium text-accent">
            {open ? "ocultar detalle ▴" : "ver detalle ▾"}
          </span>
        </div>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="flex flex-col gap-3 border-t border-tool-border-inner bg-surface p-[14px]">
          <div className="flex flex-col gap-[5px]">
            <div className="text-[10.5px] font-semibold uppercase tracking-[.14em]
                             text-text-tertiary">
              Herramienta
            </div>
            <div className="font-mono text-[13px] text-navy">{toolCall.name}</div>
          </div>
          <div className="flex flex-col gap-[5px]">
            <div className="text-[10.5px] font-semibold uppercase tracking-[.14em]
                             text-text-tertiary">
              Argumentos
            </div>
            <pre className="overflow-auto rounded-[7px] bg-navy p-[12px_14px] font-mono
                             text-[12.5px] leading-[1.6] text-accent-lighter">
              {JSON.stringify(toolCall.arguments, null, 2)}
            </pre>
          </div>
          <div className="flex flex-col gap-[5px]">
            <div className="text-[10.5px] font-semibold uppercase tracking-[.14em]
                             text-text-tertiary">
              Resultado
            </div>
            <pre className="overflow-auto rounded-[7px] border border-border bg-[#F5F7F9]
                             p-[12px_14px] font-mono text-[12.5px] leading-[1.6] text-text-body">
              {JSON.stringify(toolCall.result, null, 2)}
            </pre>
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
