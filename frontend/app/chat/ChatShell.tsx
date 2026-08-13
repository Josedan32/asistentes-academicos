"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useRequireRole } from "@/lib/hooks/useRequireRole";
import { useChatStream } from "@/lib/hooks/useChatStream";
import { getMe } from "@/lib/api/me";
import { getConversation } from "@/lib/api/conversations";
import type { ActiveAssistant } from "@/lib/assistant-identity";
import { Sidebar } from "./Sidebar";
import { ChatHeader } from "./ChatHeader";
import { MessageThread } from "./MessageThread";
import { StatusBanner } from "./StatusBanner";
import { Composer } from "./Composer";
import { FeedbackControls } from "./FeedbackControls";

export function ChatShell({
  initialConversationId = null,
}: {
  initialConversationId?: number | null;
}) {
  useRequireRole("student");
  const router = useRouter();
  const meQuery = useQuery({ queryKey: ["me"], queryFn: getMe });
  const [activeAssistant, setActiveAssistant] = useState<ActiveAssistant>({ type: "general" });

  const courseId = activeAssistant.type === "course" ? activeAssistant.courseId : null;
  const stream = useChatStream(courseId);

  useEffect(() => {
    if (initialConversationId === null) return;
    // Already have this exact conversation in memory — e.g. we just sent the first message of a
    // new conversation and the URL-sync effect below replaced /chat with /chat/{id}. Refetching
    // here would discard the in-flight state for no reason.
    if (stream.conversationId === initialConversationId) return;
    let cancelled = false;
    getConversation(initialConversationId).then((detail) => {
      if (cancelled) return;
      stream.loadConversation(detail);
      setActiveAssistant(
        detail.course_id !== null
          ? { type: "course", courseId: detail.course_id, courseName: detail.course_name ?? "" }
          : { type: "general" }
      );
    });
    return () => {
      cancelled = true;
    };
    // Runs once per navigated conversation id; `stream` intentionally excluded — it is stable
    // across renders (its setters are useCallback-memoized) and re-including it would refetch
    // on every state change this same effect causes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialConversationId]);

  useEffect(() => {
    // A brand-new conversation (started from the bare /chat route) just got its first real,
    // persisted id from the backend's `done` event. Sync the URL to /chat/{id} so a reload — or
    // sharing the link — doesn't lose it; the conversation itself was already saved server-side
    // the whole time, only the browser's address bar was stale.
    if (initialConversationId === null && stream.conversationId !== null) {
      router.replace(`/chat/${stream.conversationId}`);
    }
  }, [initialConversationId, stream.conversationId, router]);

  function handleSelectAssistant(next: ActiveAssistant) {
    stream.reset();
    setActiveAssistant(next);
    router.push("/chat");
  }

  function handleNewConversation() {
    stream.reset();
    router.push("/chat");
  }

  function handleSelectConversation(conversationId: number) {
    router.push(`/chat/${conversationId}`);
  }

  return (
    <div className="grid h-screen grid-cols-[288px_1fr] grid-rows-[100%] overflow-hidden">
      <Sidebar
        activeAssistant={activeAssistant}
        onSelectAssistant={handleSelectAssistant}
        onNewConversation={handleNewConversation}
        activeConversationId={stream.conversationId}
        onSelectConversation={handleSelectConversation}
      />
      <div className="flex min-h-0 min-w-0 flex-col bg-app-bg">
        <ChatHeader
          activeAssistant={activeAssistant}
          runState={stream.runState}
          mode={stream.mode}
          onModeChange={stream.setMode}
          showModeSelector={activeAssistant.type === "course"}
        />

        <div className="flex-1 overflow-auto py-7">
          <div className="mx-auto flex max-w-[800px] flex-col gap-[22px] px-6">
            <MessageThread
              messages={stream.messages}
              activeAssistant={activeAssistant}
              runState={stream.runState}
              studentFirstName={meQuery.data?.first_name ?? ""}
              onSuggestedQuestion={(text) => stream.send(text)}
              feedbackSlot={(message) => (
                <FeedbackControls message={message} onFeedbackSubmitted={stream.applyFeedback} />
              )}
              mode={stream.mode}
              onSubmitAnswer={(answer) => stream.send(answer)}
            />
          </div>
        </div>

        <div className="flex-none border-t border-border bg-surface px-6 py-4">
          <div className="mx-auto flex max-w-[800px] flex-col gap-3">
            <StatusBanner
              runState={stream.runState} queuedInfo={stream.queuedInfo}
              thinkingTool={stream.thinkingTool} errorInfo={stream.errorInfo}
              onStop={stream.stop} onRetry={stream.clearError}
            />
            <Composer runState={stream.runState} onSend={stream.send} onStop={stream.stop} />
          </div>
        </div>
      </div>
    </div>
  );
}
