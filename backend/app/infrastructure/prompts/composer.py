from pathlib import Path

from app.application.agents.dto import StudentContext

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
PROMPT_VERSION = "v1"


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
        ).strip()
        return prompt, version
