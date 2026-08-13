from pathlib import Path

from app.application.agents.dto import StudentContext
from app.domain.agents.modes import ChatMode

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
PROMPT_VERSION = "v1"

MODE_INSTRUCTIONS: dict[ChatMode, str] = {
    ChatMode.CONSULTA: "",
    ChatMode.ESTUDIO: (
        "Modo estudio: explica el tema paso a paso, construyendo desde lo mas basico antes "
        "de lo avanzado. No des solo la respuesta corta; ensena el razonamiento completo."
    ),
    ChatMode.PRACTICA: (
        "Modo practica: busca un ejercicio real en el material del curso con "
        "search_course_material y presentaselo al estudiante tal cual aparece, sin "
        "inventarlo. Cuando el estudiante responda, retroalimenta si acerto o no, y si es "
        "un ejercicio matematico explica la solucion paso a paso."
    ),
    ChatMode.EXAMEN: (
        "Modo examen: el estudiante quiere prepararse para un examen sobre un tema que el "
        "mismo indica. Busca ejercicios reales de ese tema en el material del curso con "
        "search_course_material, uno a la vez, y retroalimenta cada respuesta antes de "
        "pasar al siguiente."
    ),
    ChatMode.RESUMEN: (
        "Modo resumen: da un resumen organizado del tema pedido a manera de hoja de "
        "estudio, no una conversacion. Usa una lista markdown con los puntos clave."
    ),
}


class TemplatePromptComposer:
    def compose_system_prompt(
        self, context: StudentContext, *, version: str = PROMPT_VERSION
    ) -> tuple[str, str]:
        template_path = TEMPLATE_DIR / f"{version}.txt"
        if not template_path.is_file():
            raise FileNotFoundError(f"no prompt template for version {version!r}")
        template = template_path.read_text(encoding="utf-8")

        active_course_line = (
            f"La conversacion esta enfocada exclusivamente en el curso "
            f"{context.active_course_name}. Solo tienes herramientas para consultar ese curso "
            f"y sus prerrequisitos. Si el estudiante pregunta por otra materia distinta, "
            f"dile que ese tema no corresponde a este asistente y que cambie de asistente en "
            f"la barra lateral; no inventes ni describas contenido de otras materias."
            if context.active_course_name
            else ""
        )
        prompt = template.format(
            program_id=context.program_id,
            semester=context.current_semester,
            active_course_line=active_course_line,
            mode_instructions=MODE_INSTRUCTIONS[context.mode],
        ).strip()
        return prompt, version
