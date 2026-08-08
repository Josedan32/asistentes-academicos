"use client";

import { useRequireRole } from "@/lib/hooks/useRequireRole";
import { AdminSidebar } from "../AdminSidebar";
import { CoursesTable } from "./CoursesTable";

export default function CoursesPage() {
  useRequireRole("coordination");
  return (
    <div className="grid min-h-screen grid-cols-[236px_1fr] bg-app-bg">
      <AdminSidebar active="courses" />
      <CoursesTable />
    </div>
  );
}
