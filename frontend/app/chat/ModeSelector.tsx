"use client";

import type { ChatMode } from "@/lib/hooks/useChatStream";

const MODES: { value: ChatMode; label: string }[] = [
  { value: "consulta", label: "Consulta" },
  { value: "estudio", label: "Estudio" },
  { value: "practica", label: "Práctica" },
  { value: "examen", label: "Examen" },
  { value: "resumen", label: "Resumen" },
];

export function ModeSelector({
  mode, onModeChange, disabled,
}: {
  mode: ChatMode;
  onModeChange: (mode: ChatMode) => void;
  disabled: boolean;
}) {
  return (
    <div className="flex flex-none items-center gap-1 rounded-control border border-border-control
                     bg-app-bg p-[3px]">
      {MODES.map((option) => (
        <button
          key={option.value}
          disabled={disabled}
          onClick={() => onModeChange(option.value)}
          className={
            option.value === mode
              ? "rounded-[6px] bg-navy px-[10px] py-[6px] text-[12.5px] font-semibold text-white"
              : "rounded-[6px] px-[10px] py-[6px] text-[12.5px] font-medium text-text-secondary " +
                "hover:bg-surface disabled:opacity-50"
          }
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
