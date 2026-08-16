"use client";

import { useQuery } from "@tanstack/react-query";
import { getMe, getChatModel } from "@/lib/api/me";
import { assistantTitle, type ActiveAssistant } from "@/lib/assistant-identity";
import { robotStateFor } from "@/lib/robot-state";
import type { ChatMode, RunState } from "@/lib/hooks/useChatStream";
import { AssistantAvatar } from "./AssistantAvatar";
import { MODES } from "./ModeSelector";

export function ChatHeader({
  activeAssistant, runState = "idle", mode,
}: {
  activeAssistant: ActiveAssistant;
  runState?: RunState;
  mode?: ChatMode;
}) {
  const meQuery = useQuery({ queryKey: ["me"], queryFn: getMe });
  const modelQuery = useQuery({ queryKey: ["chat-model"], queryFn: getChatModel });

  const contextLine = [meQuery.data?.program_name, modelQuery.data?.model]
    .filter(Boolean)
    .join(" · ");
  const modeLabel = MODES.find((option) => option.value === mode)?.label;

  return (
    <div className="flex h-[66px] flex-none items-center justify-between gap-4 border-b
                     border-border bg-surface px-6">
      <div className="flex min-w-0 items-center gap-3">
        <AssistantAvatar state={robotStateFor(runState)} size={34} />
        <div className="min-w-0">
          <div className="text-[15px] font-semibold leading-[1.2] text-navy">
            {assistantTitle(activeAssistant)}
          </div>
          <div className="text-[12.5px] leading-[1.3] text-text-secondary">{contextLine}</div>
        </div>
      </div>
      {activeAssistant.type === "course" && modeLabel && (
        <span className="flex-none rounded-pill border border-border-control bg-app-bg
                          px-3 py-[6px] text-[12.5px] font-medium text-text-secondary">
          Modo actual del asistente: <span className="font-semibold text-navy">{modeLabel}</span>
        </span>
      )}
    </div>
  );
}
