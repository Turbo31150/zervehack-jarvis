"""
JARVIS-ZERO: Build Anything with Local AI Agents
ZerveHack 2026 — $10,000 AI Hackathon

Turn any idea into a running multi-agent system in seconds.
No cloud. No limits. No excuses.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents import AnalysisAgent, CodeAgent, ResearchAgent, SynthesisAgent
from agents.base import AgentInput, AgentOutput, BaseAgent

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="JARVIS-ZERO: Build Anything with Local AI Agents",
    description=(
        "Turn any idea into a running multi-agent system in seconds — no cloud, no limits. "
        "Orchestrates specialized AI agents in parallel using local LLMs (Ollama / LM Studio). "
        "Built for ZerveHack 2026."
    ),
    version="2.0.0",
    contact={"name": "Turbo31150", "url": "https://github.com/Turbo31150"},
    license_info={"name": "MIT"},
)

_ALLOWED_ORIGINS = ["*"]  # hackathon demo — lock down for production

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store"
    return response


logger = logging.getLogger("jarvis-zero")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

# ---------------------------------------------------------------------------
# Local LLM backend (Ollama / LM Studio)
# ---------------------------------------------------------------------------

LOCAL_LLM_BACKENDS = [
    {
        "name": "lmstudio-m1",
        "url": "http://192.168.1.85:1234/v1/chat/completions",
        "model": "qwen3.5-9b",
    },
    {
        "name": "ollama-local",
        "url": "http://127.0.0.1:11434/v1/chat/completions",
        "model": "gemma3:4b",
    },
]


async def query_local_llm(
    prompt: str, system: str = "You are a helpful AI assistant."
) -> str:
    """
    Query the first available local LLM backend.
    Falls back through the backend list automatically.
    No cloud API keys required.
    """
    payload = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 512,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        for backend in LOCAL_LLM_BACKENDS:
            try:
                body = {**payload, "model": backend["model"]}
                resp = await client.post(backend["url"], json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    logger.info(
                        "LLM response from %s (%d chars)", backend["name"], len(content)
                    )
                    return content
            except Exception as exc:
                logger.warning("Backend %s unavailable: %s", backend["name"], exc)
    return "[LLM unavailable — running in offline mode]"


# ---------------------------------------------------------------------------
# Agent registry
# ---------------------------------------------------------------------------

SPECIALIST_AGENTS: list[BaseAgent] = [
    ResearchAgent(),
    CodeAgent(),
    AnalysisAgent(),
]
SYNTHESIS_AGENT = SynthesisAgent()
ALL_AGENTS: list[BaseAgent] = SPECIALIST_AGENTS + [SYNTHESIS_AGENT]
AGENT_MAP: dict[str, BaseAgent] = {a.name: a for a in ALL_AGENTS}

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class OrchestrateRequest(BaseModel):
    task: str = Field(
        ..., min_length=3, max_length=2000, description="The idea or task to build"
    )
    context: str = Field("", max_length=4000, description="Optional additional context")
    min_confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Minimum agent confidence threshold"
    )
    use_llm: bool = Field(
        False, description="Augment agent outputs with local LLM reasoning"
    )


class OrchestrateResponse(BaseModel):
    request_id: str
    task: str
    total_agents_invoked: int
    total_time_ms: float
    synthesis: dict[str, Any]
    agent_outputs: list[dict[str, Any]]
    llm_insight: str | None = None
    orchestrator_version: str = "2.0.0"


class DirectAgentRequest(BaseModel):
    task: str = Field(..., min_length=3, max_length=2000)
    context: str = Field("", max_length=4000)


class AgentInfo(BaseModel):
    name: str
    description: str
    version: str
    capabilities: list[str]
    status: str = "healthy"


class HealthResponse(BaseModel):
    status: str
    agents: dict[str, str]
    llm_backends: list[str]
    uptime_note: str


# ---------------------------------------------------------------------------
# OrchestratorAgent
# ---------------------------------------------------------------------------


class OrchestratorAgent:
    """
    1. Classify the task and score each specialist agent.
    2. Run selected agents IN PARALLEL via asyncio.gather().
    3. Optionally augment with a local LLM reasoning step.
    4. SynthesisAgent combines all outputs.
    """

    name = "orchestrator"
    version = "2.0.0"

    def _select_agents(
        self, task: str, min_confidence: float
    ) -> list[tuple[BaseAgent, float]]:
        scored = [(agent, agent.score_relevance(task)) for agent in SPECIALIST_AGENTS]
        scored.sort(key=lambda x: x[1], reverse=True)
        above = [(a, s) for a, s in scored if s >= min_confidence]
        return above if len(above) >= 2 else scored[:2]

    async def orchestrate(
        self,
        task: str,
        context: str,
        min_confidence: float,
        request_id: str,
        use_llm: bool,
    ) -> OrchestrateResponse:
        wall_start = time.perf_counter()

        selected = self._select_agents(task, min_confidence)
        agent_inputs = [
            AgentInput(task=task, context=context, request_id=request_id)
            for _ in selected
        ]

        # All specialist agents run in parallel
        raw_outputs: list[AgentOutput | BaseException] = await asyncio.gather(
            *[agent.run(inp) for (agent, _), inp in zip(selected, agent_inputs)],
            return_exceptions=True,
        )

        successful: list[dict[str, Any]] = []
        for out in raw_outputs:
            if isinstance(out, BaseException):
                logger.warning("Agent failed: %s", out)
                continue
            successful.append(out.model_dump())

        if not successful:
            raise HTTPException(
                status_code=500, detail="All agents failed to produce output"
            )

        # Optional local LLM augmentation
        llm_insight: str | None = None
        if use_llm:
            prompt = (
                f"Task: {task}\n\n"
                f"Agent outputs summary:\n{json.dumps(successful, indent=2)[:1500]}\n\n"
                "Provide a concise strategic insight or next action in 2-3 sentences."
            )
            llm_insight = await query_local_llm(
                prompt, system="You are JARVIS-ZERO, a local AI build assistant."
            )

        synthesis_input = AgentInput(
            task=task, context=json.dumps(successful), request_id=request_id
        )
        synthesis_out: AgentOutput = await SYNTHESIS_AGENT.run(synthesis_input)

        total_ms = round((time.perf_counter() - wall_start) * 1000, 2)

        return OrchestrateResponse(
            request_id=request_id,
            task=task,
            total_agents_invoked=len(successful),
            total_time_ms=total_ms,
            synthesis=synthesis_out.result,
            agent_outputs=successful,
            llm_insight=llm_insight,
        )


_orchestrator = OrchestratorAgent()

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/orchestrate", response_model=OrchestrateResponse, tags=["Orchestration"])
async def orchestrate(request: OrchestrateRequest) -> OrchestrateResponse:
    """
    Main endpoint: turn any idea into multi-agent output.

    - Agents run IN PARALLEL (asyncio.gather)
    - Set `use_llm=true` to augment with local LLM reasoning (Ollama/LM Studio)
    - No cloud APIs required
    """
    request_id = str(uuid.uuid4())
    return await _orchestrator.orchestrate(
        task=request.task,
        context=request.context,
        min_confidence=request.min_confidence,
        request_id=request_id,
        use_llm=request.use_llm,
    )


@app.post("/agent/research", response_model=dict, tags=["Direct Agent Calls"])
async def call_research(request: DirectAgentRequest) -> dict:
    """Directly invoke the ResearchAgent."""
    out = await AGENT_MAP["research_agent"].run(
        AgentInput(task=request.task, context=request.context)
    )
    return out.model_dump()


@app.post("/agent/code", response_model=dict, tags=["Direct Agent Calls"])
async def call_code(request: DirectAgentRequest) -> dict:
    """Directly invoke the CodeAgent."""
    out = await AGENT_MAP["code_agent"].run(
        AgentInput(task=request.task, context=request.context)
    )
    return out.model_dump()


@app.post("/agent/analyze", response_model=dict, tags=["Direct Agent Calls"])
async def call_analysis(request: DirectAgentRequest) -> dict:
    """Directly invoke the AnalysisAgent."""
    out = await AGENT_MAP["analysis_agent"].run(
        AgentInput(task=request.task, context=request.context)
    )
    return out.model_dump()


@app.post("/build", response_model=OrchestrateResponse, tags=["Build"])
async def quick_build(task: str, use_llm: bool = True) -> OrchestrateResponse:
    """
    One-liner build endpoint. Pass `task` as a query param.
    Perfect for rapid prototyping and demos.

    Example: POST /build?task=create+a+REST+API+for+inventory+management&use_llm=true
    """
    request_id = str(uuid.uuid4())
    return await _orchestrator.orchestrate(
        task=task,
        context="",
        min_confidence=0.0,
        request_id=request_id,
        use_llm=use_llm,
    )


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health() -> HealthResponse:
    """Health check — verifies all agents and lists LLM backends."""
    checks = await asyncio.gather(
        *[
            agent.run(AgentInput(task="health check", context=""))
            for agent in ALL_AGENTS
        ],
        return_exceptions=True,
    )
    statuses = {
        agent.name: ("healthy" if not isinstance(result, Exception) else "degraded")
        for agent, result in zip(ALL_AGENTS, checks)
    }
    overall = (
        "healthy" if all(v == "healthy" for v in statuses.values()) else "degraded"
    )
    return HealthResponse(
        status=overall,
        agents=statuses,
        llm_backends=[b["name"] for b in LOCAL_LLM_BACKENDS],
        uptime_note="Stateless agents, no restart needed",
    )


@app.get("/agents", response_model=list[AgentInfo], tags=["System"])
async def list_agents() -> list[AgentInfo]:
    """List all available agents with capabilities."""
    return [
        AgentInfo(
            name=a.name,
            description=a.description,
            version=a.version,
            capabilities=a.capabilities,
        )
        for a in ALL_AGENTS
    ]


@app.get("/", tags=["System"])
async def root() -> dict:
    return {
        "project": "JARVIS-ZERO: Build Anything with Local AI Agents",
        "hackathon": "ZerveHack 2026",
        "tagline": "Turn any idea into a running multi-agent system in seconds — no cloud, no limits",
        "docs": "/docs",
        "quick_build": "POST /build?task=your+idea+here",
        "orchestrate": "POST /orchestrate",
        "version": "2.0.0",
    }


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
