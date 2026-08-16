"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useRequireRole } from "@/lib/hooks/useRequireRole";
import { useChatStream } from "@/lib/hooks/useChatStream";
import { getMe } from "@/lib/api/me";
import { getConversation } from "@/lib/api/conversations";
import { getSessionAssistant, setSessionAssistant } from "@/lib/chat-session-state";
import type { ActiveAssistant } from "@/lib/assistant-identity";
import { Sidebar } from "./Sidebar";
import { ChatHeader } from "./ChatHeader";
import { MessageThread } from "./MessageThread";
import { StatusBanner } from "./StatusBanner";
import { Composer } from "./Composer";
import { FeedbackControls } from "./FeedbackControls";
import { ModeSelector } from "./ModeSelector";

export function ChatShell({
  initialConversationId = null,
}: {
  initialConversationId?: number | null;
}) {
  useRequireRole("student");
  const router = useRouter();
  const meQuery = useQuery({ queryKey: ["me"], queryFn: getMe });
  const [activeAssistant, setActiveAssistantState] = useState<ActiveAssistant>(
    () => getSessionAssistant()
  );
  const setActiveAssistant = useCallback((next: ActiveAssistant) => {
    setSessionAssistant(next);
    setActiveAssistantState(next);
  }, []);

  const courseId = activeAssistant.type === "course" ? activeAssistant.courseId : null;
  const stream = useChatStream(courseId);

  const scrollRef = useRef<HTMLDivElement>(null);
  const stickToBottomRef = useRef(true);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    function handleScroll() {
      const distanceFromBottom = el!.scrollHeight - el!.scrollTop - el!.clientHeight;
      stickToBottomRef.current = distanceFromBottom < 80;
    }
    el.addEventListener("scroll", handleScroll);
    return () => el.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || !stickToBottomRef.current) return;
    el.scrollTop = el.scrollHeight;
  }, [stream.messages]);

  useEffect(() => {
    if (initialConversationId === null) return;
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialConversationId]);

  useEffect(() => {
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
        <ChatHeader activeAssistant={activeAssistant} runState={stream.runState} />

        <div ref={scrollRef} className="flex-1 overflow-auto py-7">
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
            <Composer
              runState={stream.runState} onSend={stream.send} onStop={stream.stop}
              modeSelector={
                activeAssistant.type === "course" ? (
                  <ModeSelector
                    mode={stream.mode} onModeChange={stream.setMode}
                    disabled={stream.runState !== "idle"}
                  />
                ) : undefined
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
}
