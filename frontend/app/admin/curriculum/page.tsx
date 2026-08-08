"use client";

import { useRequireRole } from "@/lib/hooks/useRequireRole";
import { AdminSidebar } from "../AdminSidebar";
import { CurriculumBoard } from "./CurriculumBoard";

export default function CurriculumPage() {
  useRequireRole("coordination");
  return (
    <div className="grid min-h-screen grid-cols-[236px_1fr] bg-app-bg">
      <AdminSidebar active="curriculum" />
      <CurriculumBoard />
    </div>
  );
}
