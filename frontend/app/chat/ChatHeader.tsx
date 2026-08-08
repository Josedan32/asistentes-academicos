"use client";

import { useQuery } from "@tanstack/react-query";
import { getMe, getChatModel } from "@/lib/api/me";
import { assistantInitials, assistantTitle, type ActiveAssistant } from "@/lib/assistant-identity";

export function ChatHeader({ activeAssistant }: { activeAssistant: ActiveAssistant }) {
  const meQuery = useQuery({ queryKey: ["me"], queryFn: getMe });
  const modelQuery = useQuery({ queryKey: ["chat-model"], queryFn: getChatModel });

  const contextLine = [meQuery.data?.program_name, modelQuery.data?.model]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="flex h-[66px] flex-none items-center justify-between gap-4 border-b
                     border-border bg-surface px-6">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-[34px] w-[34px] flex-none items-center justify-center
                         rounded-control bg-navy text-[13px] font-semibold text-white">
          {assistantInitials(activeAssistant)}
        </div>
        <div className="min-w-0">
          <div className="text-[15px] font-semibold leading-[1.2] text-navy">
            {assistantTitle(activeAssistant)}
          </div>
          <div className="text-[12.5px] leading-[1.3] text-text-secondary">{contextLine}</div>
        </div>
      </div>
    </div>
  );
}
