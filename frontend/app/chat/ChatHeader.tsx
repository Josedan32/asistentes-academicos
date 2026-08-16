"use client";

import { useQuery } from "@tanstack/react-query";
import { Menu } from "lucide-react";
import { getMe, getChatModel } from "@/lib/api/me";
import { assistantTitle, type ActiveAssistant } from "@/lib/assistant-identity";
import { robotStateFor } from "@/lib/robot-state";
import type { ChatMode, RunState } from "@/lib/hooks/useChatStream";
import { AssistantAvatar } from "./AssistantAvatar";
import { MODES } from "./ModeSelector";

export function ChatHeader({
  activeAssistant, runState = "idle", mode, onOpenSidebar,
}: {
  activeAssistant: ActiveAssistant;
  runState?: RunState;
  mode?: ChatMode;
  onOpenSidebar?: () => void;
}) {
  const meQuery = useQuery({ queryKey: ["me"], queryFn: getMe });
  const modelQuery = useQuery({ queryKey: ["chat-model"], queryFn: getChatModel });

  const contextLine = [meQuery.data?.program_name, modelQuery.data?.model]
    .filter(Boolean)
    .join(" · ");
  const modeLabel = MODES.find((option) => option.value === mode)?.label;

  return (
    <div className="flex h-[66px] flex-none items-center justify-between gap-3 border-b
                     border-border bg-surface px-4 sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          onClick={onOpenSidebar}
          aria-label="Abrir menú"
          className="flex h-9 w-9 flex-none items-center justify-center rounded-control
                     text-text-secondary hover:bg-app-bg md:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
        <AssistantAvatar state={robotStateFor(runState)} size={34} />
        <div className="min-w-0">
          <div className="truncate text-[15px] font-semibold leading-[1.2] text-navy">
            {assistantTitle(activeAssistant)}
          </div>
          <div className="truncate text-[12.5px] leading-[1.3] text-text-secondary">
            {contextLine}
          </div>
        </div>
      </div>
      {activeAssistant.type === "course" && modeLabel && (
        <span className="hidden flex-none rounded-pill border border-border-control bg-app-bg
                          px-3 py-[6px] text-[12.5px] font-medium text-text-secondary sm:flex">
          Modo actual del asistente: <span className="font-semibold text-navy">{modeLabel}</span>
        </span>
      )}
    </div>
  );
}
