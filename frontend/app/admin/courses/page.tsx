"use client";

import { useRequireRole } from "@/lib/hooks/useRequireRole";
import { AdminSidebar } from "../AdminSidebar";
import { CoursesTable } from "./CoursesTable";

export default function CoursesPage() {
  useRequireRole("coordination");
  return (
    <div className="grid h-screen grid-cols-[236px_1fr] overflow-hidden bg-app-bg">
      <AdminSidebar active="courses" />
      <CoursesTable />
    </div>
  );
}
