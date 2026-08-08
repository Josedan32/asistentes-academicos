import type { RobotState } from "@/lib/robot-state";

const ANIMATION_BY_STATE: Record<RobotState, string> = {
  waiting: "animate-robot-breathe",
  loading: "animate-robot-breathe",
  searching: "animate-robot-bob",
  thinking: "animate-robot-bob",
  success: "animate-robot-bounce",
  error: "",
};

const LABEL_BY_STATE: Record<RobotState, string> = {
  waiting: "Asistente en espera",
  loading: "Cargando el modelo",
  searching: "Consultando la base de datos",
  thinking: "Redactando la respuesta",
  success: "Asistente listo",
  error: "El asistente tuvo un problema",
};

export function AssistantAvatar({
  state, size = 34,
}: {
  state: RobotState;
  size?: number;
}) {
  return (
    <img
      src={`/robot/${state}.svg`}
      alt={LABEL_BY_STATE[state]}
      title={LABEL_BY_STATE[state]}
      width={size}
      height={size}
      className={`flex-none ${ANIMATION_BY_STATE[state]}`}
    />
  );
}
