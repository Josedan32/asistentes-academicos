"""The spike's parsing helper is pure and load-bearing for Plan 2's Ollama adapter."""

import importlib.util
from pathlib import Path
from types import ModuleType

SPIKE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "spike_tool_calling.py"


def load_spike() -> ModuleType:
    spec = importlib.util.spec_from_file_location("spike_tool_calling", SPIKE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extracts_name_and_arguments() -> None:
    payload = {
        "message": {
            "tool_calls": [
                {
                    "function": {
                        "name": "get_prerequisites",
                        "arguments": {"program_id": 1, "course": "Base de Datos 2"},
                    }
                }
            ]
        }
    }
    name, arguments = load_spike().extract_tool_call(payload)
    assert name == "get_prerequisites"
    assert arguments == {"program_id": 1, "course": "Base de Datos 2"}


def test_arguments_arrive_as_a_mapping_not_a_json_string() -> None:
    """Ollama differs from the OpenAI wire format here. Plan 2's adapter relies on it."""
    payload = {
        "message": {
            "tool_calls": [
                {"function": {"name": "list_semester_courses", "arguments": {"semester": 4}}}
            ]
        }
    }
    _, arguments = load_spike().extract_tool_call(payload)
    assert isinstance(arguments, dict)


def test_returns_nothing_when_the_model_answered_without_a_tool() -> None:
    payload = {"message": {"content": "Claro, te explico."}}
    assert load_spike().extract_tool_call(payload) == (None, None)


def test_returns_nothing_when_tool_calls_is_empty() -> None:
    payload = {"message": {"content": "", "tool_calls": []}}
    assert load_spike().extract_tool_call(payload) == (None, None)


def test_returns_nothing_when_tool_calls_is_null() -> None:
    payload = {"message": {"content": "", "tool_calls": None}}
    assert load_spike().extract_tool_call(payload) == (None, None)
