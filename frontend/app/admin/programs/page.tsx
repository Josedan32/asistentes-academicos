"use client";

import { useRequireRole } from "@/lib/hooks/useRequireRole";
import { AdminSidebar } from "../AdminSidebar";
import { ProgramsTable } from "./ProgramsTable";

export default function ProgramsPage() {
  useRequireRole("coordination");
  return (
    <div className="grid min-h-screen grid-cols-[236px_1fr] bg-app-bg">
      <AdminSidebar active="programs" />
      <ProgramsTable />
    </div>
  );
}
