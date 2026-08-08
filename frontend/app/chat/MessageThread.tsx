"use client";

import type { ChatMessage } from "@/lib/hooks/useChatStream";
import { ToolCallCard } from "./ToolCallCard";
import { EmptyState } from "./EmptyState";

export function MessageThread({
  messages, assistantInitials, studentFirstName, onSuggestedQuestion, feedbackSlot,
}: {
  messages: ChatMessage[];
  assistantInitials: string;
  studentFirstName: string;
  onSuggestedQuestion: (text: string) => void;
  feedbackSlot?: (message: ChatMessage) => React.ReactNode;
}) {
  if (messages.length === 0) {
    return (
      <EmptyState studentFirstName={studentFirstName} onSuggestedQuestion={onSuggestedQuestion} />
    );
  }

  return (
    <div className="flex flex-col gap-[22px]">
      {messages.map((message) =>
        message.role === "user" ? (
          <div key={message.id} className="flex justify-end">
            <div className="max-w-[78%] rounded-[14px_14px_4px_14px] bg-navy p-[13px_17px]
                             text-[15.5px] leading-[1.55] text-white">
              {message.content}
            </div>
          </div>
        ) : (
          <div key={message.id} className="flex items-start gap-3">
            <div className="flex h-8 w-8 flex-none items-center justify-center rounded-control
                             bg-navy text-[12px] font-semibold text-white">
              {assistantInitials}
            </div>
            <div className="flex min-w-0 flex-1 flex-col gap-3">
              {message.toolCalls.map((toolCall, index) => (
                <ToolCallCard key={toolCall.id} toolCall={toolCall} defaultOpen={index === 0} />
              ))}

              {message.content && (
                <div className="rounded-[14px_14px_14px_4px] border border-border bg-surface
                                 p-[16px_18px] text-[15.5px] leading-[1.65] text-text-body">
                  {message.content}
                </div>
              )}

              {message.content && typeof message.id === "number" && (
                <div className="flex items-center gap-2 pl-[2px]">
                  {feedbackSlot?.(message)}
                  {message.toolCalls.length > 0 && (
                    <span className="pl-1 text-[12.5px] text-text-tertiary">
                      {message.toolCalls.length}{" "}
                      {message.toolCalls.length === 1 ? "herramienta" : "herramientas"}
                      {message.totalMs !== undefined &&
                        ` · ${(message.totalMs / 1000).toFixed(1)} s`}
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
        )
      )}
    </div>
  );
}
