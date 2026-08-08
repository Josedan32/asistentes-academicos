"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getStoredSession } from "@/lib/api/auth";

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    const session = getStoredSession();
    if (session === null) {
      router.replace("/login");
    } else {
      router.replace(session.role === "student" ? "/chat" : "/admin/programs");
    }
  }, [router]);

  return null;
}
