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
            f"un tema que pertenezca claramente a otra materia (por ejemplo ingles, otras "
            f"asignaturas o cultura general ajena a este curso), aunque lo sepas de memoria "
            f"y aunque el estudiante insista. Ante una pregunta sobre un tema de otra "
            f"materia, responde unicamente que ese tema no corresponde a este asistente y "
            f"que cambie de asistente en la barra lateral.\n"
            f"Esta regla NUNCA aplica a preguntas de seguimiento sobre algo que tu mismo ya "
            f"explicaste, mostraste o calculaste en esta conversacion — por ejemplo "
            f"'explicame la formula', 'no entendi ese paso', 'dame otro ejemplo', 'por que "
            f"da eso': esas siempre son sobre el contenido de {context.active_course_name} "
            f"y debes responderlas de una vez, sin rechazarlas ni pedir que cambien de "
            f"asistente.\n"
            f"Ejemplo de rechazo correcto: el estudiante escribe 'explicame el pasado "
            f"perfecto en ingles', un tema que nunca se menciono en la conversacion; tu "
            f"unica respuesta valida es decir que no corresponde a este asistente y sugerir "
            f"cambiar de asistente en la barra lateral.\n"
            f"Ejemplo de respuesta correcta (esto NO se rechaza): ya mostraste una formula o "
            f"un ejercicio de {context.active_course_name} y el estudiante escribe "
            f"'explicame la formula' o 'explicamela'; debes explicarla, porque es una "
            f"pregunta sobre el contenido de este curso, no de otra materia."
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
