import pytest

from app.application.agents.dto import StudentContext
from app.infrastructure.prompts.composer import PROMPT_VERSION, TemplatePromptComposer


def test_interpolates_semester() -> None:
    composer = TemplatePromptComposer()
    prompt, version = composer.compose_system_prompt(
        StudentContext(program_id=1, current_semester=4)
    )
    assert "semestre 4" in prompt
    assert version == PROMPT_VERSION


def test_never_exposes_program_id_to_the_model() -> None:
    """qwen2.5:3b does not reliably pull program_id out of the system prompt and instead
    asks the student for it (observed in production) — the prompt no longer mentions it at
    all, matching every tool now injecting it server-side instead."""
    composer = TemplatePromptComposer()
    prompt, _ = composer.compose_system_prompt(StudentContext(program_id=1, current_semester=4))
    assert "program_id" not in prompt


def test_includes_the_active_course_when_present() -> None:
    composer = TemplatePromptComposer()
    prompt, _ = composer.compose_system_prompt(
        StudentContext(program_id=1, current_semester=4, active_course_name="Base de Datos 2")
    )
    assert "Base de Datos 2" in prompt


def test_omits_the_active_course_line_when_absent() -> None:
    composer = TemplatePromptComposer()
    prompt, _ = composer.compose_system_prompt(StudentContext(program_id=1, current_semester=4))
    assert "curso" not in prompt.lower()


def test_carries_the_grounding_rule() -> None:
    composer = TemplatePromptComposer()
    prompt, _ = composer.compose_system_prompt(StudentContext(program_id=1, current_semester=4))
    assert "no devuelve resultados" in prompt


def test_unknown_version_raises() -> None:
    composer = TemplatePromptComposer()
    context = StudentContext(program_id=1, current_semester=4)
    with pytest.raises(FileNotFoundError):
        composer.compose_system_prompt(context, version="v99")
