import pytest

from app.domain.agents.entities import (
    Conversation,
    FeedbackValue,
    Message,
    MessageFeedback,
    MessageRole,
    ToolCall,
)


def test_conversation_rejects_a_blank_title() -> None:
    with pytest.raises(ValueError, match="title"):
        Conversation(user_id=1, course_id=None, title="   ")


def test_conversation_round_trips_fields() -> None:
    conversation = Conversation(user_id=1, course_id=7, title="Materias del semestre")
    assert conversation.id is None
    assert conversation.course_id == 7


def test_message_role_accepts_only_user_or_assistant() -> None:
    assert MessageRole("user") is MessageRole.USER
    with pytest.raises(ValueError):
        MessageRole("tool")


def test_message_round_trips_fields() -> None:
    message = Message(conversation_id=1, role=MessageRole.ASSISTANT, content="hola",
                       prompt_version="v1")
    assert message.id is None
    assert message.role is MessageRole.ASSISTANT


def test_tool_call_rejects_a_sequence_below_one() -> None:
    with pytest.raises(ValueError, match="sequence"):
        ToolCall(message_id=1, name="get_prerequisites", arguments={}, result=None,
                  duration_ms=10, row_count=0, sequence=0)


def test_tool_call_rejects_a_negative_duration() -> None:
    with pytest.raises(ValueError, match="duration"):
        ToolCall(message_id=1, name="get_prerequisites", arguments={}, result=None,
                  duration_ms=-1, row_count=0, sequence=1)


def test_tool_call_round_trips_fields() -> None:
    call = ToolCall(message_id=1, name="get_prerequisites", arguments={"course": "BD2"},
                     result={"prerequisites": []}, duration_ms=120, row_count=0, sequence=1)
    assert call.name == "get_prerequisites"


def test_message_feedback_value_is_up_or_down() -> None:
    feedback = MessageFeedback(message_id=1, value=FeedbackValue.UP)
    assert feedback.comment is None
    with pytest.raises(ValueError):
        FeedbackValue("meh")
