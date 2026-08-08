"use client";

import { useCallback, useRef, useState } from "react";
import { streamChat } from "@/lib/api/chat-stream";
import type { ConversationDetailOut } from "@/lib/types";

export type RunState = "idle" | "queued" | "loading_model" | "thinking" | "streaming" | "error";

export interface ChatToolCall {
  id: string | number;
  name: string;
  arguments: Record<string, unknown>;
  result: unknown;
  duration_ms: number;
  row_count: number;
}

export interface ChatFeedback {
  value: "up" | "down";
  comment: string | null;
}

export interface ChatMessage {
  id: string | number;
  role: "user" | "assistant";
  content: string;
  toolCalls: ChatToolCall[];
  feedback: ChatFeedback | null;
  totalMs?: number;
  sourceCount?: number;
}

export interface QueuedInfo {
  position: number;
  estimatedWait: number;
}

export interface ErrorInfo {
  code: string;
  message: string;
}

export function useChatStream(courseId: number | null) {
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [runState, setRunState] = useState<RunState>("idle");
  const [queuedInfo, setQueuedInfo] = useState<QueuedInfo | null>(null);
  const [thinkingTool, setThinkingTool] = useState<string | null>(null);
  const [errorInfo, setErrorInfo] = useState<ErrorInfo | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const toolSequenceRef = useRef(0);
  const sendingRef = useRef(false);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    sendingRef.current = false;
    setConversationId(null);
    setMessages([]);
    setRunState("idle");
    setQueuedInfo(null);
    setThinkingTool(null);
    setErrorInfo(null);
  }, []);

  const loadConversation = useCallback((detail: ConversationDetailOut) => {
    abortRef.current?.abort();
    sendingRef.current = false;
    setConversationId(detail.id);
    setMessages(
      detail.messages.map((message) => ({
        id: message.id, role: message.role, content: message.content,
        toolCalls: message.tool_calls.map((toolCall) => ({
          id: toolCall.id, name: toolCall.name, arguments: toolCall.arguments,
          result: toolCall.result, duration_ms: toolCall.duration_ms,
          row_count: toolCall.row_count,
        })),
        feedback: message.feedback,
      }))
    );
    setRunState("idle");
    setQueuedInfo(null);
    setThinkingTool(null);
    setErrorInfo(null);
  }, []);

  const applyFeedback = useCallback((messageId: string | number, feedback: ChatFeedback) => {
    setMessages((prev) =>
      prev.map((message) => (message.id === messageId ? { ...message, feedback } : message))
    );
  }, []);

  const send = useCallback(
    async (text: string) => {
      // Guards against sending a second message while the first is still in flight — e.g. a
      // student typing "Hola" while the previous turn is still loading the model. Without
      // this, both requests reach the backend with the same (still-null) conversation_id and
      // each creates its own conversation server-side, producing exactly the "some messages
      // never get a visible reply" symptom this was written to fix. `runState` isn't a
      // dependency here on purpose — the check must see the *current* value at call time, not
      // the value from whenever this closure was created.
      if (sendingRef.current) return;
      sendingRef.current = true;

      setErrorInfo(null);
      const userMessageId = `local-user-${Date.now()}`;
      const assistantMessageId = `local-assistant-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        { id: userMessageId, role: "user", content: text, toolCalls: [], feedback: null },
        { id: assistantMessageId, role: "assistant", content: "", toolCalls: [], feedback: null },
      ]);
      setRunState("thinking");

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        await streamChat(
          { conversation_id: conversationId, course_id: courseId, message: text },
          (event) => {
            switch (event.event) {
              case "queued":
                setRunState("queued");
                setQueuedInfo({
                  position: event.data.position, estimatedWait: event.data.estimated_wait,
                });
                break;
              case "loading_model":
                setRunState("loading_model");
                break;
              case "thinking":
                setRunState("thinking");
                setThinkingTool(event.data.tool);
                break;
              case "tool_call":
                setRunState("thinking");
                toolSequenceRef.current += 1;
                setMessages((prev) =>
                  prev.map((message) =>
                    message.id === assistantMessageId
                      ? {
                          ...message,
                          toolCalls: [
                            ...message.toolCalls,
                            {
                              id: `${assistantMessageId}-tool-${toolSequenceRef.current}`,
                              name: event.data.name, arguments: event.data.arguments,
                              result: event.data.result, duration_ms: event.data.duration_ms,
                              row_count: event.data.row_count,
                            },
                          ],
                        }
                      : message
                  )
                );
                break;
              case "token":
                setRunState("streaming");
                setMessages((prev) =>
                  prev.map((message) =>
                    message.id === assistantMessageId
                      ? { ...message, content: message.content + event.data.text }
                      : message
                  )
                );
                break;
              case "done":
                setRunState("idle");
                setThinkingTool(null);
                setQueuedInfo(null);
                setConversationId(event.data.conversation_id);
                setMessages((prev) =>
                  prev.map((message) =>
                    message.id === assistantMessageId
                      ? {
                          ...message,
                          id: event.data.message_id,
                          totalMs: event.data.total_ms,
                          sourceCount: event.data.source_count,
                        }
                      : message
                  )
                );
                break;
              case "error":
                setRunState("error");
                setErrorInfo({ code: event.data.code, message: event.data.message });
                break;
            }
          },
          controller.signal
        );
      } catch (caught) {
        if ((caught as Error).name !== "AbortError") {
          setRunState("error");
          setErrorInfo({
            code: "network_error", message: "No se pudo conectar con el asistente.",
          });
        } else {
          setRunState("idle");
        }
      } finally {
        sendingRef.current = false;
      }
    },
    [conversationId, courseId]
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const clearError = useCallback(() => {
    setRunState("idle");
    setErrorInfo(null);
  }, []);

  return {
    conversationId, messages, runState, queuedInfo, thinkingTool, errorInfo,
    send, stop, reset, loadConversation, applyFeedback, clearError,
  };
}
