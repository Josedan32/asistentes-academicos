"""Test doubles for the agents module. See spec §12: a fake LLMProvider is what makes
the loop testable without a model running."""

from dataclasses import dataclass, field

from app.application.agents.llm_types import LLMMessage, LLMResponse


@dataclass
class FakeLLMProvider:
    responses: list[LLMResponse]
    model: str = "fake-v1"
    loaded: bool = True
    calls: list[list[LLMMessage]] = field(default_factory=list)

    async def is_loaded(self) -> bool:
        return self.loaded

    async def complete(
        self, messages: list[LLMMessage], tools: list | None = None
    ) -> LLMResponse:
        self.calls.append(messages)
        if len(self.calls) > len(self.responses):
            raise AssertionError(
                f"FakeLLMProvider called {len(self.calls)} times but only "
                f"{len(self.responses)} responses were scripted"
            )
        return self.responses[len(self.calls) - 1]
