"use client";

import { useState } from "react";
import { submitFeedback } from "@/lib/api/feedback";
import type { ChatFeedback, ChatMessage } from "@/lib/hooks/useChatStream";

function CopyButton({ content }: { content: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => {
        await navigator.clipboard.writeText(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className="h-8 rounded-[7px] border border-border px-3 text-[12.5px] font-medium
                 text-text-secondary hover:border-accent hover:text-navy"
    >
      {copied ? "Copiado" : "Copiar"}
    </button>
  );
}

export function FeedbackControls({
  message, onFeedbackSubmitted,
}: {
  message: ChatMessage;
  onFeedbackSubmitted: (messageId: number, feedback: ChatFeedback) => void;
}) {
  const [pendingValue, setPendingValue] = useState<"up" | "down" | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (message.feedback) {
    return (
      <>
        <span className="flex h-8 w-8 items-center justify-center rounded-[7px] border
                          border-border text-[14px]">
          {message.feedback.value === "up" ? "👍" : "👎"}
        </span>
        <CopyButton content={message.content} />
      </>
    );
  }

  async function finalize(includeComment: boolean) {
    if (pendingValue === null || typeof message.id !== "number") return;
    setSubmitting(true);
    const payload: ChatFeedback = {
      value: pendingValue, comment: includeComment ? comment.trim() || null : null,
    };
    try {
      await submitFeedback(message.id, payload);
      onFeedbackSubmitted(message.id, payload);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <button
          onClick={() => setPendingValue("up")}
          className={
            pendingValue === "up"
              ? "flex h-8 w-8 items-center justify-center rounded-[7px] border border-accent " +
                "text-[14px]"
              : "flex h-8 w-8 items-center justify-center rounded-[7px] border border-border " +
                "text-[14px] hover:border-accent"
          }
        >
          👍
        </button>
        <button
          onClick={() => setPendingValue("down")}
          className={
            pendingValue === "down"
              ? "flex h-8 w-8 items-center justify-center rounded-[7px] border " +
                "border-error-accent text-[14px]"
              : "flex h-8 w-8 items-center justify-center rounded-[7px] border border-border " +
                "text-[14px] hover:border-error-accent"
          }
        >
          👎
        </button>
        <CopyButton content={message.content} />
      </div>

      {pendingValue && (
        <div className="flex flex-col gap-[10px] rounded-card-lg border border-border-control
                         bg-surface p-[14px]">
          <div className="text-[13px] font-semibold text-navy">
            ¿Qué le faltó a esta respuesta?{" "}
            <span className="font-normal text-text-tertiary">(opcional)</span>
          </div>
          <textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Ej.: no mencionó que Redes choca en horario"
            className="min-h-16 resize-y rounded-control border border-border-control
                       p-[10px_12px] text-[14px] leading-[1.5] text-navy outline-none
                       focus-visible:border-accent"
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={() => finalize(false)} disabled={submitting}
              className="h-[34px] rounded-[7px] border border-border-control bg-surface
                         px-[14px] text-[13px] font-medium text-text-secondary"
            >
              Omitir
            </button>
            <button
              onClick={() => finalize(true)} disabled={submitting}
              className="h-[34px] rounded-[7px] bg-navy px-4 text-[13px] font-semibold text-white"
            >
              Enviar comentario
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
