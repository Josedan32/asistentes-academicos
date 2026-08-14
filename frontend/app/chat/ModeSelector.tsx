"use client";

import { Check, SlidersHorizontal } from "lucide-react";
import { DropdownMenu } from "radix-ui";
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
  const activeLabel = MODES.find((option) => option.value === mode)?.label ?? "Consulta";

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          disabled={disabled}
          aria-label={`Modo del asistente: ${activeLabel}`}
          title={`Modo: ${activeLabel}`}
          className="flex h-10 w-10 flex-none items-center justify-center rounded-[9px] border
                     border-border-control bg-app-bg text-text-secondary hover:bg-surface
                     disabled:opacity-50"
        >
          <SlidersHorizontal className="h-[17px] w-[17px]" />
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="start"
          side="top"
          sideOffset={8}
          className="z-50 min-w-[168px] rounded-[10px] border border-border bg-surface p-1
                     shadow-lg"
        >
          {MODES.map((option) => (
            <DropdownMenu.Item
              key={option.value}
              onSelect={() => onModeChange(option.value)}
              className="flex cursor-pointer items-center justify-between gap-2 rounded-[7px]
                         px-[10px] py-[8px] text-[13.5px] font-medium text-navy outline-none
                         hover:bg-app-bg data-[highlighted]:bg-app-bg"
            >
              {option.label}
              {option.value === mode && <Check className="h-[14px] w-[14px] text-accent" />}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
