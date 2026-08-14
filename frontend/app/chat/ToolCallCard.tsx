"use client";

import { Settings2 } from "lucide-react";
import { describeToolCall } from "@/lib/describe-tool-call";
import type { ChatToolCall } from "@/lib/hooks/useChatStream";

/** Never exposes `toolCall.arguments` / `toolCall.result` — those can carry raw student or
 * course data pulled straight from the database, and this card renders in a UI students can
 * screenshot and share. Only the pre-approved Spanish description from describeToolCall and
 * timing/row-count metadata are shown, with no way to expand into the raw payload. */
export function ToolCallCard({ toolCall }: { toolCall: ChatToolCall }) {
  const description = describeToolCall(toolCall.name, toolCall.arguments);
  const hasNoRows = toolCall.row_count === 0;

  return (
    <div className="flex items-center gap-[10px] rounded-card-lg border border-tool-border
                     bg-tool-bg px-[14px] py-[11px]">
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
    </div>
  );
}
