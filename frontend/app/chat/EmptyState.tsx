"use client";

import type { ActiveAssistant } from "@/lib/assistant-identity";
import { suggestedQuestionsFor } from "@/lib/suggested-questions";
import { AssistantAvatar } from "./AssistantAvatar";

export function EmptyState({
  activeAssistant, studentFirstName, onSuggestedQuestion,
}: {
  activeAssistant: ActiveAssistant;
  studentFirstName: string;
  onSuggestedQuestion: (text: string) => void;
}) {
  const suggestions = suggestedQuestionsFor(activeAssistant);

  return (
    <div className="flex flex-col items-center gap-[26px] pt-[60px] text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-[14px] bg-navy p-2">
        <AssistantAvatar state="success" size={44} />
      </div>
      <div className="flex flex-col gap-2">
        <h2 className="m-0 text-[26px] font-bold leading-[1.15] text-navy">
          Hola, {studentFirstName}.
        </h2>
        <p className="m-0 max-w-[460px] text-[16px] leading-[1.55] text-text-secondary">
          {activeAssistant.type === "general"
            ? "Puedo consultar tu malla, tus prerrequisitos y los créditos de tu carrera. " +
              "Prueba con una de estas:"
            : `Puedo ayudarte con ${activeAssistant.courseName}. Prueba con una de estas:`}
        </p>
      </div>
      <div className="grid w-full grid-cols-2 gap-3 text-left">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => onSuggestedQuestion(suggestion)}
            className="rounded-card-lg border border-border bg-surface p-[16px_18px]
                       text-left text-[14.5px] font-medium leading-[1.4] text-navy
                       hover:border-accent hover:bg-[#F2F6FA]"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
