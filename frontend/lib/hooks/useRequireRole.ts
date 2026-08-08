"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getStoredSession } from "../api/auth";

export function useRequireRole(role: "student" | "coordination"): void {
  const router = useRouter();

  useEffect(() => {
    const session = getStoredSession();
    if (session === null || session.role !== role) {
      router.replace("/login");
    }
  }, [router, role]);
}
