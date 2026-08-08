import { apiFetch, setStoredToken, getStoredToken } from "./client";
import type { TokenOut } from "../types";

const ROLE_STORAGE_KEY = "pb_role";

export interface Session {
  token: string;
  role: "student" | "coordination";
}

export interface RegisterPayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  document: string;
  program_id: number;
  current_semester: number;
}

function persistSession(token: TokenOut): void {
  setStoredToken(token.access_token);
  if (typeof window !== "undefined") {
    localStorage.setItem(ROLE_STORAGE_KEY, token.role);
  }
}

export async function login(email: string, password: string): Promise<Session> {
  const token = await apiFetch<TokenOut>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  persistSession(token);
  return { token: token.access_token, role: token.role };
}

export async function register(payload: RegisterPayload): Promise<Session> {
  const token = await apiFetch<TokenOut>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  persistSession(token);
  return { token: token.access_token, role: token.role };
}

export function logout(): void {
  setStoredToken(null);
  if (typeof window !== "undefined") {
    localStorage.removeItem(ROLE_STORAGE_KEY);
  }
}

export function getStoredSession(): Session | null {
  const token = getStoredToken();
  if (typeof window === "undefined" || !token) return null;
  const role = localStorage.getItem(ROLE_STORAGE_KEY);
  if (role !== "student" && role !== "coordination") return null;
  return { token, role };
}
