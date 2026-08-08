"use client";

import type { ActiveAssistant } from "@/lib/assistant-identity";
import type { ChatMessage, RunState } from "@/lib/hooks/useChatStream";
import { robotStateFor } from "@/lib/robot-state";
import { AssistantMessage } from "./AssistantMessage";
import { EmptyState } from "./EmptyState";

const BUSY_STATES: RunState[] = ["loading_model", "thinking", "queued", "streaming"];

export function MessageThread({
  messages, activeAssistant, runState = "idle", studentFirstName, onSuggestedQuestion,
  feedbackSlot,
}: {
  messages: ChatMessage[];
  activeAssistant: ActiveAssistant;
  runState?: RunState;
  studentFirstName: string;
  onSuggestedQuestion: (text: string) => void;
  feedbackSlot?: (message: ChatMessage) => React.ReactNode;
}) {
  if (messages.length === 0) {
    return (
      <EmptyState activeAssistant={activeAssistant} studentFirstName={studentFirstName}
                  onSuggestedQuestion={onSuggestedQuestion} />
    );
  }

  const lastMessageId = messages[messages.length - 1]?.id;

  return (
    <div className="flex flex-col gap-[22px]">
      {messages.map((message) => {
        if (message.role === "user") {
          return (
            <div key={message.id} className="flex justify-end">
              <div className="max-w-[78%] rounded-[14px_14px_4px_14px] bg-navy p-[13px_17px]
                               text-[15.5px] leading-[1.55] text-white">
                {message.content}
              </div>
            </div>
          );
        }

        const isActive = message.id === lastMessageId && BUSY_STATES.includes(runState);
        return (
          <AssistantMessage
            key={message.id}
            message={message}
            avatarState={isActive ? robotStateFor(runState) : "success"}
            isStreaming={isActive && runState === "streaming"}
            feedbackSlot={feedbackSlot}
          />
        );
      })}
    </div>
  );
}
