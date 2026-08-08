"use client";

import { useCallback, useState } from "react";
import * as authApi from "../api/auth";
import type { Session } from "../api/auth";

export function useAuth() {
  const [session, setSession] = useState<Session | null>(() => authApi.getStoredSession());

  const login = useCallback(async (email: string, password: string) => {
    const next = await authApi.login(email, password);
    setSession(next);
    return next;
  }, []);

  const register = useCallback(async (payload: authApi.RegisterPayload) => {
    const next = await authApi.register(payload);
    setSession(next);
    return next;
  }, []);

  const logout = useCallback(() => {
    authApi.logout();
    setSession(null);
  }, []);

  return { session, login, register, logout };
}
