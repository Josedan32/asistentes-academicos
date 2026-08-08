"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { listCurriculum, listPrograms } from "@/lib/api/programs";
import { describeAssistants } from "@/lib/assistant-preview";
import { useAuth } from "@/lib/hooks/useAuth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const SEMESTERS = Array.from({ length: 10 }, (_, index) => index + 1);

export function RegisterForm() {
  const router = useRouter();
  const { register } = useAuth();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [document, setDocument] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [programId, setProgramId] = useState<number | null>(null);
  const [semester, setSemester] = useState(1);
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const programsQuery = useQuery({ queryKey: ["programs"], queryFn: listPrograms });
  const curriculumQuery = useQuery({
    queryKey: ["curriculum", programId, semester],
    queryFn: () => listCurriculum(programId as number, semester),
    enabled: programId !== null,
  });

  const selectedProgram = programsQuery.data?.find((program) => program.id === programId);

  const previewText = useMemo(() => {
    if (!selectedProgram) return null;
    return describeAssistants(
      selectedProgram.name, semester, (curriculumQuery.data ?? []).map((course) => course.name)
    );
  }, [selectedProgram, semester, curriculumQuery.data]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    if (programId === null) {
      setError("Selecciona tu carrera.");
      return;
    }
    if (!consent) {
      setError("Debes aceptar el tratamiento de datos para continuar.");
      return;
    }

    setSubmitting(true);
    try {
      await register({
        email, password, first_name: firstName, last_name: lastName, document,
        program_id: programId, current_semester: semester,
      });
      router.push("/chat");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.detail : "No se pudo crear la cuenta.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-[720px] max-w-full flex-col gap-7">
      <div className="flex flex-col gap-2">
        <h1 className="m-0 text-[32px] font-bold leading-[1.1] text-navy">
          Crear cuenta de estudiante
        </h1>
        <p className="m-0 text-[16px] leading-[1.55] text-text-secondary">
          Tu carrera y tu semestre definen a qué materias y a qué asistentes tendrás acceso.
        </p>
      </div>

      <div className="flex flex-col gap-5 rounded-container border border-border bg-surface p-7">
        <div className="text-[11px] font-semibold uppercase tracking-[.14em] text-text-tertiary">
          Datos personales
        </div>
        <div className="grid grid-cols-2 gap-4">
          <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
            Nombres
            <Input required value={firstName}
                   onChange={(event) => setFirstName(event.target.value)}
                   className="h-11 rounded-control border-border-control px-[14px] text-[15px]" />
          </label>
          <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
            Apellidos
            <Input required value={lastName}
                   onChange={(event) => setLastName(event.target.value)}
                   className="h-11 rounded-control border-border-control px-[14px] text-[15px]" />
          </label>
          <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
            Documento
            <Input required value={document}
                   onChange={(event) => setDocument(event.target.value)}
                   className="h-11 rounded-control border-border-control px-[14px] text-[15px]" />
          </label>
          <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
            Correo institucional
            <Input type="email" required value={email}
                   onChange={(event) => setEmail(event.target.value)}
                   className="h-11 rounded-control border-border-control px-[14px] text-[15px]" />
          </label>
          <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
            Contraseña
            <Input type="password" required minLength={8} value={password}
                   onChange={(event) => setPassword(event.target.value)}
                   className="h-11 rounded-control border-border-control px-[14px] text-[15px]" />
          </label>
          <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
            Confirmar contraseña
            <Input type="password" required minLength={8} value={confirmPassword}
                   onChange={(event) => setConfirmPassword(event.target.value)}
                   className="h-11 rounded-control border-border-control px-[14px] text-[15px]" />
          </label>
        </div>
      </div>

      <div className="flex flex-col gap-5 rounded-container border border-accent-lighter
                       bg-surface p-7 shadow-[0_1px_0_var(--color-accent)_inset,0_0_0_3px_rgba(29,91,150,.05)]">
        <div className="flex items-baseline justify-between gap-4">
          <div className="text-[11px] font-semibold uppercase tracking-[.14em] text-accent">
            Contexto académico
          </div>
          <div className="text-[13px] text-text-secondary">
            Define las materias que verá tu asistente
          </div>
        </div>

        <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
          Carrera
          <select
            required
            value={programId ?? ""}
            onChange={(event) => setProgramId(Number(event.target.value) || null)}
            className="h-11 rounded-control border border-border-control bg-surface px-3
                       text-[15px] text-navy"
          >
            <option value="" disabled>Selecciona tu carrera</option>
            {(programsQuery.data ?? []).map((program) => (
              <option key={program.id} value={program.id}>{program.name}</option>
            ))}
          </select>
        </label>

        <div className="flex flex-col gap-[10px]">
          <div className="text-[13px] font-semibold text-text-label">Semestre actual</div>
          <div className="flex flex-wrap gap-2">
            {SEMESTERS.map((value) => (
              <button
                type="button"
                key={value}
                onClick={() => setSemester(value)}
                className={
                  value === semester
                    ? "h-11 w-[52px] rounded-control border border-navy bg-navy text-[15px] " +
                      "font-semibold text-white"
                    : "h-11 w-[52px] rounded-control border border-border-control bg-surface " +
                      "text-[15px] font-medium text-text-label hover:border-accent"
                }
              >
                {value}
              </button>
            ))}
          </div>
        </div>

        {previewText && (
          <div className="flex items-start gap-3 rounded-control bg-[#F2F6FA] p-[14px_16px]">
            <div className="flex h-[22px] w-[22px] flex-none items-center justify-center
                             rounded-full bg-accent text-[13px] font-semibold text-white">
              i
            </div>
            <p className="m-0 text-[14px] leading-[1.5] text-text-label">{previewText}</p>
          </div>
        )}
      </div>

      {error && <p className="m-0 text-[14px] text-error-accent">{error}</p>}

      <div className="flex items-center justify-between pb-5">
        <label className="flex max-w-[420px] cursor-pointer items-center gap-[9px] text-[14px]
                           text-text-secondary">
          <input type="checkbox" checked={consent}
                 onChange={(event) => setConsent(event.target.checked)}
                 className="h-[15px] w-[15px] flex-none accent-accent" />
          Acepto el tratamiento de datos y que mis conversaciones se usen para evaluar el
          asistente.
        </label>
        <Button type="submit" disabled={submitting}
                className="h-12 rounded-control bg-navy px-[30px] text-[15px] font-semibold
                           text-white hover:bg-navy-hover">
          Crear cuenta
        </Button>
      </div>
    </form>
  );
}
