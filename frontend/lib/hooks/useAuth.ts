"use client";

import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import * as authApi from "../api/auth";
import type { Session } from "../api/auth";

export function useAuth() {
  const [session, setSession] = useState<Session | null>(() => authApi.getStoredSession());
  const queryClient = useQueryClient();

  const login = useCallback(async (email: string, password: string) => {
    queryClient.clear();
    const next = await authApi.login(email, password);
    setSession(next);
    return next;
  }, [queryClient]);

  const register = useCallback(async (payload: authApi.RegisterPayload) => {
    queryClient.clear();
    const next = await authApi.register(payload);
    setSession(next);
    return next;
  }, [queryClient]);

  const logout = useCallback(() => {
    authApi.logout();
    setSession(null);
    queryClient.clear();
  }, [queryClient]);

  return { session, login, register, logout };
}
