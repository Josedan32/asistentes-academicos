"""Risk probe: measure tool-selection reliability of the local model.

Run with `backend/.venv/Scripts/python.exe backend/scripts/spike_tool_calling.py`.
Requires a running Ollama with qwen2.5:3b pulled.

`extract_tool_call` is pure and covered by tests/scripts/test_spike_tool_calling.py;
the network path is not tested, since that would be testing Ollama.
"""

import asyncio
import json

import httpx

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:3b"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_semester_courses",
            "description": "List the courses a student takes in a given semester of a program.",
            "parameters": {
                "type": "object",
                "properties": {
                    "program_id": {"type": "integer", "description": "Program identifier"},
                    "semester": {"type": "integer", "description": "Semester number, 1 to 10"},
                },
                "required": ["program_id", "semester"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_prerequisites",
            "description": "Get the prerequisites of a course within a program.",
            "parameters": {
                "type": "object",
                "properties": {
                    "program_id": {"type": "integer", "description": "Program identifier"},
                    "course": {"type": "string", "description": "Course name as the student wrote it"},
                },
                "required": ["program_id", "course"],
            },
        },
    },
]

SYSTEM = (
    "Eres un asistente academico de la Institucion Universitaria Pascual Bravo. "
    "El estudiante cursa el programa con program_id=1, semestre 4. "
    "Usa siempre una herramienta para responder preguntas sobre materias, "
    "prerrequisitos o creditos. Nunca respondas de memoria."
)

CASES: list[tuple[str, str]] = [
    ("Que materias veo este semestre?", "list_semester_courses"),
    ("Cuales son los prerrequisitos de Base de Datos 2?", "get_prerequisites"),
    ("Que necesito antes de ver Ingenieria de Software 1?", "get_prerequisites"),
    ("Dame el listado de asignaturas del semestre 5", "list_semester_courses"),
    ("Que debo aprobar primero para Herramientas de Programacion 2?", "get_prerequisites"),
]


def extract_tool_call(payload: dict) -> tuple[str | None, dict | None]:
    """Pull the first tool call out of an Ollama /api/chat response.

    Ollama returns `arguments` as an object; the OpenAI wire format returns a JSON
    string. Callers must not json.loads the result. Plan 2's adapter depends on this.
    """
    tool_calls = payload.get("message", {}).get("tool_calls") or []
    if not tool_calls:
        return None, None
    function = tool_calls[0]["function"]
    return function["name"], function.get("arguments")


async def call_model(client: httpx.AsyncClient, question: str) -> dict:
    response = await client.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": question},
            ],
            "tools": TOOLS,
            "stream": False,
            "keep_alive": "10m",
            "options": {"num_ctx": 8192, "temperature": 0},
        },
        timeout=180.0,
    )
    response.raise_for_status()
    return response.json()


async def main() -> None:
    hits = 0
    total = 0
    async with httpx.AsyncClient() as client:
        for question, expected_tool in CASES:
            for attempt in range(3):
                total += 1
                payload = await call_model(client, question)
                chosen, arguments = extract_tool_call(payload)
                ok = chosen == expected_tool
                hits += ok
                mark = "OK " if ok else "MISS"
                print(f"[{mark}] run {attempt + 1} | {question}")
                print(f"       expected={expected_tool} got={chosen} args={json.dumps(arguments)}")

    print(f"\nTool selection accuracy: {hits}/{total} = {hits / total:.0%}")


if __name__ == "__main__":
    asyncio.run(main())
