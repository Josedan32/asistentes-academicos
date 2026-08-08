import { LoginForm } from "./LoginForm";

export default function LoginPage() {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <div className="flex flex-col justify-between bg-navy p-16 text-white">
        <div className="w-fit rounded-lg bg-white p-[14px_18px]">
          <img src="/logo-wordmark.svg" alt="Institución Universitaria Pascual Bravo"
               className="block h-11" />
        </div>
        <div className="flex max-w-[440px] flex-col gap-5">
          <div className="text-[12px] font-semibold uppercase tracking-[.18em] text-accent-light">
            Asistente académico
          </div>
          <h1 className="m-0 text-[46px] font-bold leading-[1.08] tracking-[-.01em]">
            Un agente que consulta tu malla, no que la inventa.
          </h1>
          <p className="m-0 text-[17px] leading-[1.6] text-accent-lighter">
            Cada respuesta muestra las herramientas que ejecutó y los datos que consultó.
          </p>
        </div>
        <div className="text-[13px] leading-[1.5] text-accent-muted">
          Facultad de Ingeniería · Medellín
        </div>
      </div>

      <div className="flex items-center justify-center bg-app-bg p-16">
        <LoginForm />
      </div>
    </div>
  );
}
