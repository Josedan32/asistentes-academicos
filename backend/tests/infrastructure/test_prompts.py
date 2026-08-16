import pytest

from app.application.agents.dto import StudentContext
from app.domain.agents.modes import ChatMode
from app.infrastructure.prompts.composer import PROMPT_VERSION, TemplatePromptComposer


def test_interpolates_semester() -> None:
    composer = TemplatePromptComposer()
    prompt, version = composer.compose_system_prompt(
        StudentContext(program_id=1, current_semester=4)
    )
    assert "semestre 4" in prompt
    assert version == PROMPT_VERSION


def test_never_exposes_program_id_to_the_model() -> None:
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


def test_active_course_line_tells_the_model_not_to_discuss_other_courses() -> None:
    composer = TemplatePromptComposer()
    prompt, _ = composer.compose_system_prompt(
        StudentContext(program_id=1, current_semester=4, active_course_name="Algebra Lineal")
    )
    assert "otra materia" in prompt.lower()


def test_enrolled_courses_are_listed_when_present() -> None:
    composer = TemplatePromptComposer()
    prompt, _ = composer.compose_system_prompt(
        StudentContext(
            program_id=1,
            current_semester=5,
            enrolled_course_names=("Algebra Lineal", "Estadistica"),
        )
    )
    assert "Algebra Lineal" in prompt
    assert "Estadistica" in prompt


def test_enrolled_courses_line_absent_when_none_matriculated() -> None:
    composer = TemplatePromptComposer()
    prompt, _ = composer.compose_system_prompt(StudentContext(program_id=1, current_semester=5))
    assert "matriculadas" not in prompt.lower()


def test_general_assistant_gets_told_to_redirect_to_the_enrolled_courses_assistant() -> None:
    composer = TemplatePromptComposer()
    prompt, _ = composer.compose_system_prompt(
        StudentContext(program_id=1, current_semester=5, enrolled_course_names=("Algebra Lineal",))
    )
    assert "cambie al asistente de esa materia" in prompt


def test_course_scoped_assistant_is_not_told_to_redirect_students_away() -> None:
    composer = TemplatePromptComposer()
    prompt, _ = composer.compose_system_prompt(
        StudentContext(
            program_id=1,
            current_semester=5,
            active_course_name="Algebra Lineal",
            enrolled_course_names=("Algebra Lineal", "Estadistica"),
        )
    )
    assert "cambie al asistente de esa materia" not in prompt


def test_unknown_version_raises() -> None:
    composer = TemplatePromptComposer()
    context = StudentContext(program_id=1, current_semester=4)
    with pytest.raises(FileNotFoundError):
        composer.compose_system_prompt(context, version="v99")


def test_each_mode_produces_different_framing_text() -> None:
    composer = TemplatePromptComposer()
    prompts = {
        mode: composer.compose_system_prompt(
            StudentContext(program_id=1, current_semester=4, mode=mode)
        )[0]
        for mode in ChatMode
    }
    assert len(set(prompts.values())) == len(ChatMode)


def test_consulta_mode_matches_the_original_unframed_prompt() -> None:
    composer = TemplatePromptComposer()
    default_prompt, _ = composer.compose_system_prompt(
        StudentContext(program_id=1, current_semester=4)
    )
    consulta_prompt, _ = composer.compose_system_prompt(
        StudentContext(program_id=1, current_semester=4, mode=ChatMode.CONSULTA)
    )
    assert default_prompt == consulta_prompt
