"use client";

import type { ChatMessage } from "@/lib/hooks/useChatStream";
import { useTypewriter } from "@/lib/hooks/useTypewriter";
import type { RobotState } from "@/lib/robot-state";
import { AssistantAvatar } from "./AssistantAvatar";
import { MarkdownContent } from "./MarkdownContent";
import { ToolCallCard } from "./ToolCallCard";

export function AssistantMessage({
  message, avatarState, isStreaming, feedbackSlot,
}: {
  message: ChatMessage;
  avatarState: RobotState;
  isStreaming: boolean;
  feedbackSlot?: (message: ChatMessage) => React.ReactNode;
}) {
  const visibleContent = useTypewriter(message.content, isStreaming);

  return (
    <div className="flex items-start gap-3">
      <AssistantAvatar size={32} state={avatarState} />
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        {message.toolCalls.map((toolCall, index) => (
          <ToolCallCard key={toolCall.id} toolCall={toolCall} defaultOpen={index === 0} />
        ))}

        {visibleContent && (
          <div className="rounded-[14px_14px_14px_4px] border border-border bg-surface
                           p-[16px_18px]">
            <MarkdownContent content={visibleContent} />
          </div>
        )}

        {message.content && typeof message.id === "number" && (
          <div className="flex items-center gap-2 pl-[2px]">
            {feedbackSlot?.(message)}
            {message.toolCalls.length > 0 && (
              <span className="pl-1 text-[12.5px] text-text-tertiary">
                {message.toolCalls.length}{" "}
                {message.toolCalls.length === 1 ? "herramienta" : "herramientas"}
                {message.totalMs !== undefined && ` · ${(message.totalMs / 1000).toFixed(1)} s`}
                {message.sourceCount !== undefined &&
                  ` · ${message.sourceCount} ${
                    message.sourceCount === 1
                      ? "fuente de la base de datos"
                      : "fuentes de la base de datos"
                  }`}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
