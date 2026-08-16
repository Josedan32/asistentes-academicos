import type { ActiveAssistant } from "./assistant-identity";
import type { ChatMode } from "./hooks/useChatStream";

let activeAssistant: ActiveAssistant = { type: "general" };
let mode: ChatMode = "consulta";

export function getSessionAssistant(): ActiveAssistant {
  return activeAssistant;
}

export function setSessionAssistant(next: ActiveAssistant): void {
  activeAssistant = next;
}

export function getSessionMode(): ChatMode {
  return mode;
}

export function setSessionMode(next: ChatMode): void {
  mode = next;
}
