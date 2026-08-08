"use client";

import { useState } from "react";
import { useRequireRole } from "@/lib/hooks/useRequireRole";
import type { ActiveAssistant } from "@/lib/assistant-identity";
import { Sidebar } from "./Sidebar";
import { ChatHeader } from "./ChatHeader";

export function ChatShell({
  initialConversationId = null,
}: {
  initialConversationId?: number | null;
}) {
  useRequireRole("student");
  const [activeAssistant, setActiveAssistant] = useState<ActiveAssistant>({ type: "general" });

  return (
    <div className="grid h-screen grid-cols-[288px_1fr] overflow-hidden">
      <Sidebar
        activeAssistant={activeAssistant}
        onSelectAssistant={setActiveAssistant}
        onNewConversation={() => {}}
        activeConversationId={initialConversationId}
        onSelectConversation={() => {}}
      />
      <div className="flex min-h-0 min-w-0 flex-col bg-app-bg">
        <ChatHeader activeAssistant={activeAssistant} />
        <div className="flex-1" />
      </div>
    </div>
  );
}
