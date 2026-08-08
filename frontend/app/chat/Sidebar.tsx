"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { LogOut } from "lucide-react";
import { getMe } from "@/lib/api/me";
import { listConversations } from "@/lib/api/conversations";
import { listCurriculum } from "@/lib/api/programs";
import { relativeDate } from "@/lib/relative-date";
import { useAuth } from "@/lib/hooks/useAuth";
import type { ActiveAssistant } from "@/lib/assistant-identity";

interface SidebarProps {
  activeAssistant: ActiveAssistant;
  onSelectAssistant: (assistant: ActiveAssistant) => void;
  onNewConversation: () => void;
  activeConversationId: number | null;
  onSelectConversation: (conversationId: number) => void;
}

export function Sidebar({
  activeAssistant, onSelectAssistant, onNewConversation, activeConversationId,
  onSelectConversation,
}: SidebarProps) {
  const router = useRouter();
  const { logout } = useAuth();
  const meQuery = useQuery({ queryKey: ["me"], queryFn: getMe });
  const curriculumQuery = useQuery({
    queryKey: ["curriculum", meQuery.data?.program_id, meQuery.data?.current_semester],
    queryFn: () =>
      listCurriculum(meQuery.data!.program_id as number, meQuery.data!.current_semester as number),
    enabled: !!meQuery.data?.program_id && !!meQuery.data?.current_semester,
  });
  const conversationsQuery = useQuery({
    queryKey: ["conversations"], queryFn: listConversations,
  });

  const initials = meQuery.data
    ? `${meQuery.data.first_name?.[0] ?? ""}${meQuery.data.last_name?.[0] ?? ""}`.toUpperCase()
    : "";

  return (
    <div className="flex min-h-0 flex-col overflow-hidden bg-navy">
      <div className="flex flex-none flex-col gap-4 px-[18px] pb-4 pt-5">
        <div className="w-fit rounded-md bg-white p-[9px_12px]">
          <img src="/logo-wordmark.svg" alt="Pascual Bravo" className="block h-[26px]" />
        </div>
        <button
          onClick={onNewConversation}
          className="flex h-[42px] items-center justify-center gap-2 rounded-control
                     border border-navy-button-border bg-navy-hover text-[14px] font-semibold
                     text-white hover:bg-[#1A4374]"
        >
          + Nueva conversación
        </button>
      </div>

      <div className="flex flex-none flex-col gap-[9px] px-[18px] pb-[14px]">
        <div className="text-[11px] font-semibold uppercase tracking-[.14em] text-accent-muted">
          Asistente
        </div>
        <div className="flex flex-col gap-1">
          <button
            onClick={() => onSelectAssistant({ type: "general" })}
            className={
              activeAssistant.type === "general"
                ? "flex items-center gap-[10px] rounded-[7px] bg-accent px-3 py-[10px] text-white"
                : "flex items-center gap-[10px] rounded-[7px] px-3 py-[9px] text-accent-lighter " +
                  "hover:bg-navy-hover"
            }
          >
            <span className="h-[7px] w-[7px] rounded-full bg-assistant-dot" />
            <span className="text-[14px] font-semibold">General de Carrera</span>
          </button>

          {meQuery.data?.current_semester != null && (
            <div className="px-3 pb-1 pt-3 text-[11px] font-medium uppercase tracking-[.1em]
                             text-accent-muted">
              Materias · semestre {meQuery.data.current_semester}
            </div>
          )}

          {(curriculumQuery.data ?? []).map((course) => {
            const isActive = activeAssistant.type === "course" &&
              activeAssistant.courseId === course.id;
            return (
              <button
                key={course.id}
                onClick={() =>
                  onSelectAssistant({ type: "course", courseId: course.id, courseName: course.name })
                }
                className={
                  isActive
                    ? "flex items-center gap-[10px] rounded-[7px] bg-accent px-3 py-[9px] text-white"
                    : "flex items-center gap-[10px] rounded-[7px] px-3 py-[9px] text-accent-lighter " +
                      "hover:bg-navy-hover"
                }
              >
                <span className="h-[7px] w-[7px] rounded-full bg-[#3F6693]" />
                <span className="text-[14px]">{course.name}</span>
              </button>
            );
          })}
        </div>
        <div className="px-3 pt-[6px] text-[12px] leading-[1.45] text-accent-muted">
          Cambiar de asistente abre una conversación nueva. No se comparte contexto entre
          materias.
        </div>
      </div>

      <div className="mx-[18px] mb-[14px] mt-[6px] h-px bg-navy-divider" />

      <div className="flex min-h-0 flex-1 flex-col gap-[2px] overflow-auto px-[18px]">
        <div className="pb-2 text-[11px] font-semibold uppercase tracking-[.14em] text-accent-muted">
          Recientes
        </div>
        {(conversationsQuery.data ?? []).map((conversation) => (
          <button
            key={conversation.id}
            onClick={() => onSelectConversation(conversation.id)}
            className={
              conversation.id === activeConversationId
                ? "rounded-[7px] bg-navy-hover px-3 py-[9px] text-left"
                : "rounded-[7px] px-3 py-[9px] text-left hover:bg-navy-hover"
            }
          >
            <div className="truncate text-[14px] font-medium text-white">
              {conversation.title}
            </div>
            <div className="pt-[3px] text-[12px] text-accent-muted">
              {conversation.course_name ?? "General"} · {relativeDate(conversation.created_at)}
            </div>
          </button>
        ))}
      </div>

      <div className="flex flex-none items-center gap-[11px] border-t border-navy-divider
                       px-[18px] py-[14px]">
        <div className="flex h-[34px] w-[34px] items-center justify-center rounded-full
                         bg-accent text-[13px] font-semibold text-white">
          {initials}
        </div>
        <div className="min-w-0">
          <div className="truncate text-[13px] font-semibold text-white">
            {meQuery.data ? `${meQuery.data.first_name} ${meQuery.data.last_name}` : ""}
          </div>
          <div className="text-[12px] text-accent-muted">
            {meQuery.data?.program_code ? `${meQuery.data.program_code} · sem ` +
              `${meQuery.data.current_semester}` : ""}
          </div>
        </div>
        <button
          onClick={() => {
            logout();
            router.push("/login");
          }}
          title="Cerrar sesión"
          aria-label="Cerrar sesión"
          className="flex h-8 w-8 flex-none items-center justify-center rounded-[7px]
                     text-accent-muted hover:bg-navy-hover hover:text-white"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
