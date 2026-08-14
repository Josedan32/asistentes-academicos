from pathlib import Path

from app.application.agents.dto import StudentContext
from app.domain.agents.modes import ChatMode

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
PROMPT_VERSION = "v1"

MODE_INSTRUCTIONS: dict[ChatMode, str] = {
    ChatMode.CONSULTA: "",
    ChatMode.ESTUDIO: (
        "Modo estudio: explica el tema paso a paso, construyendo desde lo mas basico antes "
        "de lo avanzado. No des solo la respuesta corta; ensena el razonamiento completo. "
        "Estructura la respuesta con subtitulos markdown (##) para cada etapa del tema, y "
        "cierra cada subtitulo con un ejemplo resuelto concreto antes de pasar al "
        "siguiente. Termina con una linea '**Para practicar:**' invitando a cambiar a modo "
        "practica sobre el mismo tema."
    ),
    ChatMode.PRACTICA: (
        "Modo practica: antes de responder con texto, siempre llama primero a "
        "search_course_material con el tema que pida el estudiante; nunca respondas con un "
        "ejercicio sin haber llamado la herramienta en ese turno. Si devuelve fragmentos, "
        "presenta el ejercicio tal cual aparece en el material, sin inventarlo. Si no "
        "devuelve fragmentos utiles, dilo explicitamente y luego propon tu propio ejercicio "
        "del tema, dejando claro que lo generaste tu y que no proviene del material del "
        "curso. Cuando el estudiante responda, retroalimenta si acerto o no, y si es un "
        "ejercicio matematico explica la solucion paso a paso."
    ),
    ChatMode.EXAMEN: (
        "Modo examen: el estudiante quiere prepararse para un examen sobre un tema que el "
        "mismo indica. Antes de responder con texto, siempre llama primero a "
        "search_course_material con ese tema; nunca respondas con un ejercicio sin haber "
        "llamado la herramienta en ese turno. Si devuelve fragmentos, usa ejercicios reales "
        "de ahi, uno a la vez, y retroalimenta cada respuesta antes de pasar al siguiente. "
        "Si no devuelve fragmentos utiles, dilo explicitamente y luego propon tu propio "
        "ejercicio del tema, dejando claro que lo generaste tu y que no proviene del "
        "material del curso."
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
            f"REGLA INQUEBRANTABLE: este asistente es exclusivo del curso "
            f"{context.active_course_name}. Nunca respondas, expliques ni des ejemplos de "
            f"ningun tema de otra materia, aunque lo sepas de memoria y aunque el "
            f"estudiante insista — incluye ingles, otras materias, cultura general o "
            f"cualquier tema fuera del contenido de este curso. Ante cualquier pregunta "
            f"que no sea sobre {context.active_course_name} o sus prerrequisitos, responde "
            f"unicamente que ese tema no corresponde a este asistente y que cambie de "
            f"asistente en la barra lateral. Solo tienes herramientas para consultar este "
            f"curso y sus prerrequisitos; no inventes ni describas contenido de otras "
            f"materias. Ejemplo obligatorio: si el estudiante escribe 'explicame el pasado "
            f"perfecto en ingles' y este curso es {context.active_course_name}, tu unica "
            f"respuesta valida es decir que ese tema no corresponde a este asistente y "
            f"sugerir cambiar de asistente en la barra lateral — nunca expliques el pasado "
            f"perfecto ni ningun otro tema fuera de {context.active_course_name}, sin "
            f"importar que tan simple o breve parezca la pregunta."
            if context.active_course_name
            else ""
        )
        enrolled_courses_line = self._enrolled_courses_line(context)
        prompt = template.format(
            program_id=context.program_id,
            semester=context.current_semester,
            active_course_line=active_course_line,
            enrolled_courses_line=enrolled_courses_line,
            mode_instructions=MODE_INSTRUCTIONS[context.mode],
        ).strip()
        return prompt, version

    @staticmethod
    def _enrolled_courses_line(context: StudentContext) -> str:
        if not context.enrolled_course_names:
            return ""
        line = (
            f"El estudiante tiene matriculadas estas materias este periodo: "
            f"{', '.join(context.enrolled_course_names)}."
        )
        if context.active_course_name:
            return line
        return line + (
            " Si pregunta algo especifico del contenido de una de esas materias, dile "
            "que cambie al asistente de esa materia en la barra lateral en vez de "
            "responder tu los detalles — tu solo tienes informacion general de la "
            "malla, no el contenido de cada materia."
        )
