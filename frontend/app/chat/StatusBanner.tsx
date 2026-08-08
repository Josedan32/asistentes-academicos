"use client";

import { Settings2 } from "lucide-react";
import type { ErrorInfo, QueuedInfo, RunState } from "@/lib/hooks/useChatStream";

const QUEUE_POSITION_LABELS: Record<number, string> = {
  1: "primer lugar", 2: "segundo lugar", 3: "tercer lugar",
};

export function StatusBanner({
  runState, queuedInfo, thinkingTool, errorInfo, onStop, onRetry,
}: {
  runState: RunState;
  queuedInfo: QueuedInfo | null;
  thinkingTool: string | null;
  errorInfo: ErrorInfo | null;
  onStop: () => void;
  onRetry: () => void;
}) {
  if (runState === "loading_model") {
    return (
      <div className="flex items-center gap-3 rounded-card-lg border border-tool-border
                       bg-tool-bg p-[12px_14px]">
        <div className="h-4 w-4 flex-none animate-spin rounded-full border-2
                         border-tool-border border-t-accent" />
        <div className="flex-1">
          <div className="text-[13.5px] font-semibold text-navy">
            Cargando el modelo en memoria
          </div>
          <div className="text-[13px] text-accent-faint">
            Primera consulta tras un rato de inactividad. Suele tardar entre 10 y 30 segundos.
          </div>
        </div>
        <div className="h-[5px] w-[120px] overflow-hidden rounded-full bg-[#DCE8F2]">
          <div className="h-full w-[45%] bg-accent" />
        </div>
      </div>
    );
  }

  if (runState === "thinking") {
    return (
      <div className="flex items-center gap-3 rounded-card-lg border border-tool-border
                       bg-tool-bg p-[12px_14px]">
        <Settings2 className="h-[14px] w-[14px] flex-none animate-pulse text-accent" />
        <div className="flex-1">
          <div className="text-[13.5px] font-semibold text-navy">
            Usando herramienta ·{" "}
            <span className="font-mono text-[13px]">{thinkingTool}</span>
          </div>
          <div className="text-[13px] text-accent-faint">
            Puede pasar varios segundos sin texto nuevo mientras consulta la base de datos.
          </div>
        </div>
        <button
          onClick={onStop}
          className="h-[34px] rounded-[7px] border border-error-accent bg-surface px-[14px]
                     text-[13px] font-semibold text-error-accent hover:bg-error-bg"
        >
          Detener
        </button>
      </div>
    );
  }

  if (runState === "queued" && queuedInfo) {
    return (
      <div className="flex items-center gap-3 rounded-card-lg border border-amber-border
                       bg-amber-bg p-[12px_14px]">
        <span className="flex h-[22px] w-[22px] flex-none items-center justify-center
                          rounded-full bg-amber-accent text-[12px] font-semibold text-white">
          {queuedInfo.position}
        </span>
        <div className="flex-1">
          <div className="text-[13.5px] font-semibold text-amber-text">
            En cola · {QUEUE_POSITION_LABELS[queuedInfo.position] ?? `lugar ${queuedInfo.position}`}
          </div>
          <div className="text-[13px] text-amber-text-muted">
            La GPU está atendiendo otra consulta. Tu turno empieza en aproximadamente{" "}
            {queuedInfo.estimatedWait} segundos.
          </div>
        </div>
        <button
          onClick={onStop}
          className="h-[34px] rounded-[7px] border border-[#D9C88E] bg-surface px-[14px]
                     text-[13px] font-semibold text-amber-text"
        >
          Cancelar
        </button>
      </div>
    );
  }

  if (runState === "error" && errorInfo) {
    return (
      <div className="flex items-start gap-3 rounded-card-lg border border-error-border
                       bg-error-bg p-[14px]">
        <span className="flex h-[22px] w-[22px] flex-none items-center justify-center
                          rounded-full bg-error-accent text-[13px] font-semibold text-white">
          !
        </span>
        <div className="flex flex-1 flex-col gap-2">
          <div className="text-[13.5px] font-semibold text-error-text">
            El asistente no está disponible en este momento
          </div>
          <div className="text-[13px] leading-[1.5] text-error-text-muted">
            {errorInfo.message || "El servicio de inferencia no responde en el servidor de la " +
              "facultad."}{" "}
            Tus conversaciones anteriores siguen disponibles para lectura.
          </div>
          <div className="flex gap-2 pt-[2px]">
            <button
              onClick={onRetry}
              className="h-[34px] rounded-[7px] bg-error-accent px-[14px] text-[13px]
                         font-semibold text-white"
            >
              Reintentar
            </button>
            <button
              className="h-[34px] rounded-[7px] border border-error-border bg-surface px-[14px]
                         text-[13px] font-semibold text-error-text"
            >
              Avisar a coordinación
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
