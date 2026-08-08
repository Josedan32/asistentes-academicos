"use client";

import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { useAuth } from "@/lib/hooks/useAuth";

const ITEMS = [
  { key: "programs", label: "Carreras", href: "/admin/programs" },
  { key: "courses", label: "Materias", href: "/admin/courses" },
  { key: "curriculum", label: "Malla curricular", href: "/admin/curriculum" },
] as const;

export function AdminSidebar({ active }: { active: (typeof ITEMS)[number]["key"] }) {
  const router = useRouter();
  const { logout } = useAuth();
  return (
    <div className="flex h-full flex-col gap-[22px] bg-navy p-4">
      <div className="w-fit rounded-md bg-white p-[9px_12px]">
        <img src="/logo-wordmark.svg" alt="Pascual Bravo" className="block h-6" />
      </div>
      <div className="text-[11px] font-semibold uppercase tracking-[.14em] text-accent-muted">
        Coordinación
      </div>
      <div className="flex flex-col gap-[3px]">
        {ITEMS.map((item) => (
          <button
            key={item.key}
            onClick={() => router.push(item.href)}
            className={
              item.key === active
                ? "rounded-[7px] bg-accent px-3 py-[10px] text-left text-[14px] font-semibold text-white"
                : "rounded-[7px] px-3 py-[10px] text-left text-[14px] text-accent-lighter hover:bg-navy-hover"
            }
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="mt-auto flex flex-col gap-[3px] border-t border-navy-divider pt-3">
        <button
          onClick={() => {
            logout();
            router.push("/login");
          }}
          className="flex items-center gap-2 rounded-[7px] px-3 py-[10px] text-left text-[14px]
                     text-accent-lighter hover:bg-navy-hover"
        >
          <LogOut className="h-4 w-4" />
          Cerrar sesión
        </button>
      </div>
    </div>
  );
}
