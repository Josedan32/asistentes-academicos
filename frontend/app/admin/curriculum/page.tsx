"use client";

import { useRequireRole } from "@/lib/hooks/useRequireRole";
import { AdminSidebar } from "../AdminSidebar";
import { CurriculumBoard } from "./CurriculumBoard";

export default function CurriculumPage() {
  useRequireRole("coordination");
  return (
    <div className="grid h-screen grid-cols-[236px_1fr] overflow-hidden bg-app-bg">
      <AdminSidebar active="curriculum" />
      <CurriculumBoard />
    </div>
  );
}
