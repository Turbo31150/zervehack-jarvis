"""Base agent interface for JARVIS multi-agent framework."""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class AgentInput(BaseModel):
    task: str
    context: str = ""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])


class AgentOutput(BaseModel):
    agent_name: str
    agent_version: str = "1.0.0"
    request_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    result: dict[str, Any]
    processing_time_ms: float
    error: str | None = None


class BaseAgent(ABC):
    name: str = "base"
    description: str = "Base agent"
    version: str = "1.0.0"
    capabilities: list[str] = []

    @abstractmethod
    async def run(self, input_data: AgentInput) -> AgentOutput:
        """Execute the agent logic and return structured output."""

    def score_relevance(self, task: str) -> float:
        """Return 0-1 confidence this agent can handle the given task."""
        task_lower = task.lower()
        hits = sum(1 for cap in self.capabilities if cap in task_lower)
        return min(hits / max(len(self.capabilities), 1), 1.0)

    def _make_output(
        self,
        input_data: AgentInput,
        result: dict[str, Any],
        confidence: float,
        start: float,
        error: str | None = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            agent_version=self.version,
            request_id=input_data.request_id,
            confidence=confidence,
            result=result,
            processing_time_ms=round((time.perf_counter() - start) * 1000, 2),
            error=error,
        )
