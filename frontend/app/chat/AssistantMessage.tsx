"use client";

import type { ChatMessage, ChatMode, ChatToolCall } from "@/lib/hooks/useChatStream";
import { useTypewriter } from "@/lib/hooks/useTypewriter";
import type { RobotState } from "@/lib/robot-state";
import { AssistantAvatar } from "./AssistantAvatar";
import { ExerciseAnswerPanel } from "./ExerciseAnswerPanel";
import { ExerciseCard } from "./ExerciseCard";
import { MarkdownContent } from "./MarkdownContent";
import { ToolCallCard } from "./ToolCallCard";

function hasFragments(toolCall: ChatToolCall): boolean {
  const fragments = (toolCall.result as { fragments?: unknown[] } | undefined)?.fragments;
  return Array.isArray(fragments) && fragments.length > 0;
}

export function AssistantMessage({
  message, avatarState, isStreaming, feedbackSlot, mode, onSubmitAnswer,
}: {
  message: ChatMessage;
  avatarState: RobotState;
  isStreaming: boolean;
  feedbackSlot?: (message: ChatMessage) => React.ReactNode;
  mode: ChatMode;
  onSubmitAnswer?: (answer: string) => void;
}) {
  const visibleContent = useTypewriter(message.content, isStreaming);
  const isExerciseMode = mode === "practica" || mode === "examen";
  const searchCall = message.toolCalls.find((tc) => tc.name === "search_course_material");
  const foundInMaterial = isExerciseMode && !!searchCall && hasFragments(searchCall);

  return (
    <div className="flex items-start gap-3">
      <AssistantAvatar size={32} state={avatarState} />
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        {message.toolCalls.map((toolCall) =>
          toolCall.name === "search_course_material" && isExerciseMode
            ? (
              <ExerciseCard
                key={toolCall.id} toolCall={toolCall}
                onSubmitAnswer={(answer) => onSubmitAnswer?.(answer)}
              />
            )
            : <ToolCallCard key={toolCall.id} toolCall={toolCall} />
        )}

        {visibleContent && (
          <div className="rounded-[14px_14px_14px_4px] border border-border bg-surface
                           p-[16px_18px]">
            <MarkdownContent content={visibleContent} />
          </div>
        )}

        {isExerciseMode && !isStreaming && !foundInMaterial && message.content && onSubmitAnswer && (
          <ExerciseAnswerPanel onSubmitAnswer={onSubmitAnswer} />
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
