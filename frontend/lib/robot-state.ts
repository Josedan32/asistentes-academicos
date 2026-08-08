import type { RunState } from "./hooks/useChatStream";

export type RobotState = "waiting" | "loading" | "searching" | "thinking" | "success" | "error";

const ROBOT_BY_RUN_STATE: Record<RunState, RobotState> = {
  idle: "waiting",
  queued: "waiting",
  loading_model: "loading",
  thinking: "searching",
  streaming: "thinking",
  error: "error",
};

export function robotStateFor(runState: RunState): RobotState {
  return ROBOT_BY_RUN_STATE[runState];
}
