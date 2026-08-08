"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const session = await login(email, password);
      router.push(session.role === "student" ? "/chat" : "/admin/programs");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.detail : "No se pudo iniciar sesión.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-[400px] flex-col gap-[26px]">
      <div className="flex flex-col gap-2">
        <h2 className="m-0 text-[30px] font-bold leading-[1.1] text-navy">Iniciar sesión</h2>
        <p className="m-0 text-[15px] leading-[1.5] text-text-secondary">
          Estudiantes y coordinación entran por aquí. El sistema redirige según el rol.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
          Correo institucional
          <Input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="h-[46px] rounded-control border-border-control px-[14px] text-[15px]
                       focus-visible:border-accent focus-visible:ring-[3px]
                       focus-visible:ring-accent/[.14]"
          />
        </label>
        <label className="flex flex-col gap-[7px] text-[13px] font-semibold text-text-label">
          Contraseña
          <Input
            type="password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="h-[46px] rounded-control border-border-control px-[14px] text-[15px]
                       focus-visible:border-accent focus-visible:ring-[3px]
                       focus-visible:ring-accent/[.14]"
          />
        </label>
      </div>

      {error && <p className="m-0 text-[14px] text-error-accent">{error}</p>}

      <div className="flex items-center justify-between">
        <label className="flex cursor-pointer items-center gap-2 text-[14px] text-text-label">
          <input type="checkbox" className="h-[15px] w-[15px] accent-accent" />
          Mantener sesión
        </label>
        <a href="#" className="text-[14px] font-medium text-accent hover:text-navy">
          Olvidé mi contraseña
        </a>
      </div>

      <Button
        type="submit"
        disabled={submitting}
        className="h-12 w-full rounded-control bg-navy text-[15px] font-semibold text-white
                   hover:bg-navy-hover"
      >
        Entrar
      </Button>

      <div className="h-px bg-border" />

      <p className="m-0 text-[14px] leading-[1.5] text-text-secondary">
        ¿Eres estudiante nuevo?{" "}
        <a href="/register" className="font-semibold text-accent hover:text-navy">
          Crear cuenta
        </a>
      </p>
    </form>
  );
}
