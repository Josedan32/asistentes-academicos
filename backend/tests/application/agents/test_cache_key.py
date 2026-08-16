from app.application.agents.cache_key import cache_key
from app.application.agents.llm_types import LLMMessage, ToolDefinition


def test_same_inputs_produce_the_same_key() -> None:
    messages = [LLMMessage(role="user", content="hola")]
    tools = [ToolDefinition(name="t", description="d", parameters={"type": "object"})]

    assert cache_key(messages, "m", tools) == cache_key(messages, "m", tools)


def test_a_changed_tool_schema_changes_the_key_even_with_the_same_tool_name() -> None:
    messages = [LLMMessage(role="user", content="hola")]
    old_schema = [
        ToolDefinition(
            name="list_semester_courses",
            description="d",
            parameters={"properties": {"program_id": {}, "semester": {}}},
        )
    ]
    new_schema = [
        ToolDefinition(
            name="list_semester_courses",
            description="d",
            parameters={"properties": {"semester": {}}},
        )
    ]

    assert cache_key(messages, "m", old_schema) != cache_key(messages, "m", new_schema)


def test_a_changed_tool_description_changes_the_key() -> None:
    messages = [LLMMessage(role="user", content="hola")]
    tools_a = [ToolDefinition(name="t", description="old", parameters={})]
    tools_b = [ToolDefinition(name="t", description="new", parameters={})]

    assert cache_key(messages, "m", tools_a) != cache_key(messages, "m", tools_b)


def test_no_tools_is_a_valid_input() -> None:
    messages = [LLMMessage(role="user", content="hola")]

    assert cache_key(messages, "m", None) == cache_key(messages, "m", [])
