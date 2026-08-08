import { RegisterForm } from "./RegisterForm";

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen flex-col bg-app-bg">
      <div className="flex h-[68px] flex-none items-center justify-between border-b
                       border-border bg-surface px-8">
        <img src="/logo-wordmark.svg" alt="Pascual Bravo" className="h-[30px]" />
        <div className="text-[14px] text-text-secondary">
          ¿Ya tienes cuenta?{" "}
          <a href="/login" className="font-semibold text-accent hover:text-navy">
            Iniciar sesión
          </a>
        </div>
      </div>
      <div className="flex flex-1 justify-center overflow-auto px-8 py-11">
        <RegisterForm />
      </div>
    </div>
  );
}
