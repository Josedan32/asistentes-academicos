from app.domain.agents.modes import ChatMode


def test_five_modes_exist() -> None:
    assert {mode.value for mode in ChatMode} == {
        "consulta", "estudio", "practica", "examen", "resumen",
    }
