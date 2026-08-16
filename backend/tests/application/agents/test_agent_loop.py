from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.agents.agent_loop import AgentLoop, DoneEvent, ToolCallEvent
from app.application.agents.dto import StudentContext
from app.application.agents.llm_types import LLMResponse, ToolCallRequest
from app.domain.agents.entities import Conversation
from app.infrastructure.persistence.academic_reader import SqlAlchemyAcademicReader
from app.infrastructure.persistence.academic_repository import normalize_name
from app.infrastructure.persistence.models import CourseModel, CurriculumEntryModel, ProgramModel
from tests.application.agents.fakes import (
    FakeEmbeddingProvider,
    FakeLLMProvider,
    FakeMaterialReader,
    FakePromptComposer,
    InMemoryConversationRepository,
)


async def _seed_reader(session: AsyncSession) -> SqlAlchemyAcademicReader:
    program = ProgramModel(code="ISW", name="Ingenieria en Software", semester_count=10)
    course = CourseModel(
        code="BD2",
        name="Base de Datos 2",
        normalized_name=normalize_name("Base de Datos 2"),
        area="Datos",
        default_credits=4,
    )
    session.add_all([program, course])
    await session.commit()
    session.add(
        CurriculumEntryModel(program_id=program.id, course_id=course.id, semester=4, credits=4)
    )
    await session.commit()
    return SqlAlchemyAcademicReader(session), program.id


def _loop(provider: FakeLLMProvider, reader, conversations=None) -> AgentLoop:
    return AgentLoop(
        provider=provider,
        reader=reader,
        conversations=conversations or InMemoryConversationRepository(),
        prompt_composer=FakePromptComposer(),
        material_reader=FakeMaterialReader(),
        embedder=FakeEmbeddingProvider(),
    )


async def test_a_final_answer_without_a_tool_call_yields_one_done_event(
    session: AsyncSession,
) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(responses=[LLMResponse(content="No hay materias.")])
    conversations = InMemoryConversationRepository()
    conversation = Conversation(id=1, user_id=1, course_id=None, title="t")

    events = [
        event
        async for event in _loop(provider, reader, conversations).run(
            conversation=conversation,
            history=[],
            user_message="Que veo?",
            context=StudentContext(program_id=program_id, current_semester=4),
        )
    ]

    assert len(events) == 1
    assert isinstance(events[0], DoneEvent)
    assert events[0].content == "No hay materias."
    assert events[0].tool_count == 0
    assert events[0].hit_iteration_cap is False
    assert [m.role.value for m in conversations.messages] == ["user", "assistant"]


async def test_done_event_carries_the_persisted_message_id(session: AsyncSession) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(responses=[LLMResponse(content="No hay materias.")])
    conversations = InMemoryConversationRepository()
    conversation = Conversation(id=1, user_id=1, course_id=None, title="t")

    events = [
        event
        async for event in _loop(provider, reader, conversations).run(
            conversation=conversation,
            history=[],
            user_message="Que veo?",
            context=StudentContext(program_id=program_id, current_semester=4),
        )
    ]

    done = next(e for e in events if isinstance(e, DoneEvent))
    assert isinstance(done.message_id, int)
    assert done.message_id == conversations.messages[-1].id


async def test_a_tool_call_then_a_final_answer_yields_thinking_tool_call_done(
    session: AsyncSession,
) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(
        responses=[
            LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(id="1", name="list_semester_courses", arguments={"semester": 4})
                ],
            ),
            LLMResponse(content="Tienes 1 materia."),
        ]
    )
    conversations = InMemoryConversationRepository()
    conversation = Conversation(id=1, user_id=1, course_id=None, title="t")

    events = [
        event
        async for event in _loop(provider, reader, conversations).run(
            conversation=conversation,
            history=[],
            user_message="Que veo este semestre?",
            context=StudentContext(program_id=program_id, current_semester=4),
        )
    ]

    assert [type(e).__name__ for e in events] == ["ThinkingEvent", "ToolCallEvent", "DoneEvent"]
    assert events[1].name == "list_semester_courses"
    assert events[1].row_count == 1
    assert events[2].content == "Tienes 1 materia."
    assert events[2].tool_count == 1
    assert len(conversations.tool_calls) == 1
    assert conversations.tool_calls[0].message_id == conversations.messages[1].id


async def test_commentary_alongside_a_tool_call_is_not_persisted_as_a_second_reply(
    session: AsyncSession,
) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(
        responses=[
            LLMResponse(
                content="Dejame revisar tus materias...",
                tool_calls=[
                    ToolCallRequest(id="1", name="list_semester_courses", arguments={"semester": 4})
                ],
            ),
            LLMResponse(content="Tienes 1 materia."),
        ]
    )
    conversations = InMemoryConversationRepository()
    conversation = Conversation(id=1, user_id=1, course_id=None, title="t")

    async for _ in _loop(provider, reader, conversations).run(
        conversation=conversation,
        history=[],
        user_message="Que veo este semestre?",
        context=StudentContext(program_id=program_id, current_semester=4),
    ):
        pass

    assistant_messages = [m for m in conversations.messages if m.role.value == "assistant"]
    assert [m.content for m in assistant_messages] == ["", "Tienes 1 materia."]


async def test_invalid_arguments_return_a_tool_error_to_the_model_not_an_exception(
    session: AsyncSession,
) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(
        responses=[
            LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="1", name="list_semester_courses", arguments={"semester": "not-an-int"}
                    )
                ],
            ),
            LLMResponse(content="No pude procesar tu solicitud."),
        ]
    )

    events = [
        event
        async for event in _loop(provider, reader).run(
            conversation=Conversation(id=1, user_id=1, course_id=None, title="t"),
            history=[],
            user_message="Que veo?",
            context=StudentContext(program_id=program_id, current_semester=4),
        )
    ]

    assert isinstance(events[-1], DoneEvent)
    second_call_messages = provider.calls[1]
    assert any(m.role == "tool" and "error" in m.content for m in second_call_messages)


@dataclass
class RaisingEmbeddingProvider:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("embedding provider unreachable")


async def test_a_failing_tool_handler_returns_a_tool_error_to_the_model_not_an_exception(
    session: AsyncSession,
) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(
        responses=[
            LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="1", name="search_course_material", arguments={"query": "algo"}
                    )
                ],
            ),
            LLMResponse(content="No pude buscar el material."),
        ]
    )
    loop = AgentLoop(
        provider=provider,
        reader=reader,
        conversations=InMemoryConversationRepository(),
        prompt_composer=FakePromptComposer(),
        material_reader=FakeMaterialReader(),
        embedder=RaisingEmbeddingProvider(),
    )

    events = [
        event
        async for event in loop.run(
            conversation=Conversation(id=1, user_id=1, course_id=5, title="t"),
            history=[],
            user_message="hola",
            context=StudentContext(program_id=program_id, current_semester=4, active_course_id=5),
        )
    ]

    assert isinstance(events[-1], DoneEvent)
    assert events[-1].content == "No pude buscar el material."
    second_call_messages = provider.calls[1]
    assert any(m.role == "tool" and "error" in m.content for m in second_call_messages)


async def test_unknown_tool_name_returns_an_error_to_the_model(session: AsyncSession) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(
        responses=[
            LLMResponse(
                content=None,
                tool_calls=[ToolCallRequest(id="1", name="does_not_exist", arguments={})],
            ),
            LLMResponse(content="ok"),
        ]
    )

    events = [
        event
        async for event in _loop(provider, reader).run(
            conversation=Conversation(id=1, user_id=1, course_id=None, title="t"),
            history=[],
            user_message="hola",
            context=StudentContext(program_id=program_id, current_semester=4),
        )
    ]

    assert isinstance(events[-1], DoneEvent)
    assert events[-1].content == "ok"


async def test_hitting_the_iteration_cap_is_recorded_and_stops_calling_the_provider(
    session: AsyncSession,
) -> None:
    reader, program_id = await _seed_reader(session)
    always_calls_a_tool = LLMResponse(
        content=None,
        tool_calls=[
            ToolCallRequest(id="1", name="list_semester_courses", arguments={"semester": 4})
        ],
    )
    provider = FakeLLMProvider(
        responses=[always_calls_a_tool, always_calls_a_tool, always_calls_a_tool]
    )

    events = [
        event
        async for event in _loop(provider, reader).run(
            conversation=Conversation(id=1, user_id=1, course_id=None, title="t"),
            history=[],
            user_message="hola",
            context=StudentContext(program_id=program_id, current_semester=4),
        )
    ]

    assert len(provider.calls) == 3
    done = events[-1]
    assert isinstance(done, DoneEvent)
    assert done.hit_iteration_cap is True


async def test_program_id_for_get_course_detail_comes_from_context_not_the_model(
    session: AsyncSession,
) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(
        responses=[
            LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="1", name="get_course_detail", arguments={"course": "Base de Datos 2"}
                    )
                ],
            ),
            LLMResponse(content="4 creditos."),
        ]
    )

    events = [
        event
        async for event in _loop(provider, reader).run(
            conversation=Conversation(id=1, user_id=1, course_id=None, title="t"),
            history=[],
            user_message="Cuantos creditos tiene BD2?",
            context=StudentContext(program_id=program_id, current_semester=4),
        )
    ]

    tool_call_event = next(e for e in events if isinstance(e, ToolCallEvent))
    assert tool_call_event.result["credits"] == 4


async def test_course_scoped_conversations_never_get_list_semester_courses(
    session: AsyncSession,
) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(responses=[LLMResponse(content="ok")])

    events = [
        event
        async for event in _loop(provider, reader).run(
            conversation=Conversation(id=1, user_id=1, course_id=5, title="t"),
            history=[],
            user_message="hola",
            context=StudentContext(program_id=program_id, current_semester=4, active_course_id=5),
        )
    ]

    assert isinstance(events[-1], DoneEvent)
    assert provider.tool_names_received[0] == {
        "get_prerequisites",
        "get_course_detail",
        "find_course_in_programs",
        "search_course_material",
        "get_academic_history",
    }


async def test_course_scoped_conversations_get_search_course_material(
    session: AsyncSession,
) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(responses=[LLMResponse(content="ok")])

    events = [
        event
        async for event in _loop(provider, reader).run(
            conversation=Conversation(id=1, user_id=1, course_id=5, title="t"),
            history=[],
            user_message="hola",
            context=StudentContext(program_id=program_id, current_semester=4, active_course_id=5),
        )
    ]

    assert isinstance(events[-1], DoneEvent)
    assert provider.tool_names_received[-1] == {
        "search_course_material",
        "get_prerequisites",
        "get_course_detail",
        "find_course_in_programs",
        "get_academic_history",
    }


async def test_general_conversations_still_get_list_semester_courses(
    session: AsyncSession,
) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(responses=[LLMResponse(content="ok")])

    events = [
        event
        async for event in _loop(provider, reader).run(
            conversation=Conversation(id=1, user_id=1, course_id=None, title="t"),
            history=[],
            user_message="hola",
            context=StudentContext(program_id=program_id, current_semester=4),
        )
    ]

    assert isinstance(events[-1], DoneEvent)
    assert provider.tool_names_received[0] == {
        "list_semester_courses",
        "get_prerequisites",
        "get_course_detail",
        "find_course_in_programs",
        "get_academic_history",
    }


async def test_a_course_scoped_conversation_rejects_a_list_semester_courses_call(
    session: AsyncSession,
) -> None:
    reader, program_id = await _seed_reader(session)
    provider = FakeLLMProvider(
        responses=[
            LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(id="1", name="list_semester_courses", arguments={"semester": 4})
                ],
            ),
            LLMResponse(content="ok"),
        ]
    )

    events = [
        event
        async for event in _loop(provider, reader).run(
            conversation=Conversation(id=1, user_id=1, course_id=5, title="t"),
            history=[],
            user_message="hola",
            context=StudentContext(program_id=program_id, current_semester=4, active_course_id=5),
        )
    ]

    assert isinstance(events[-1], DoneEvent)
    second_call_messages = provider.calls[1]
    assert any(m.role == "tool" and "unknown tool" in m.content for m in second_call_messages)
