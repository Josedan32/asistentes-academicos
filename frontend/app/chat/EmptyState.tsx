"use client";

const SUGGESTIONS = [
  "¿Qué prerrequisitos me faltan para ver Base de Datos 2?",
  "¿Qué materias puedo matricular en semestre 6?",
  "¿Qué materias comparte mi carrera con Ing. Electrónica?",
  "¿Cuáles son los prerrequisitos de Sistemas Operativos?",
];

export function EmptyState({
  studentFirstName, onSuggestedQuestion,
}: {
  studentFirstName: string;
  onSuggestedQuestion: (text: string) => void;
}) {
  return (
    <div className="flex flex-col items-center gap-[26px] pt-[60px] text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-[14px] bg-navy
                       text-[18px] font-semibold text-white">
        GC
      </div>
      <div className="flex flex-col gap-2">
        <h2 className="m-0 text-[26px] font-bold leading-[1.15] text-navy">
          Hola, {studentFirstName}.
        </h2>
        <p className="m-0 max-w-[460px] text-[16px] leading-[1.55] text-text-secondary">
          Puedo consultar tu malla, tus prerrequisitos y los créditos de tu carrera. Prueba con
          una de estas:
        </p>
      </div>
      <div className="grid w-full grid-cols-2 gap-3 text-left">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => onSuggestedQuestion(suggestion)}
            className="rounded-card-lg border border-border bg-surface p-[16px_18px]
                       text-left text-[14.5px] font-medium leading-[1.4] text-navy
                       hover:border-accent hover:bg-[#F2F6FA]"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
