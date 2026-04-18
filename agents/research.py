"""ResearchAgent — simulates knowledge retrieval and web research."""

from __future__ import annotations

import asyncio
import time

from .base import AgentInput, AgentOutput, BaseAgent

KNOWLEDGE_BASE: dict[str, dict] = {
    "ai": {
        "summary": "Artificial Intelligence encompasses machine learning, deep learning, and autonomous systems.",
        "key_facts": [
            "Transformer architecture (2017) revolutionized NLP",
            "GPT-4 has ~1.8T parameters (estimated)",
            "Multi-agent systems enable complex task decomposition",
            "Reinforcement Learning drives autonomous decision-making",
        ],
        "sources": ["arxiv:2307.09288", "openai.com/research", "deepmind.com"],
    },
    "multi-agent": {
        "summary": "Multi-agent systems coordinate specialized AI agents to solve complex problems collaboratively.",
        "key_facts": [
            "AutoGPT pioneered autonomous agent loops",
            "CrewAI popularized role-based agent teams",
            "LangGraph enables stateful agent workflows",
            "Parallel execution reduces latency by 60-80%",
        ],
        "sources": ["arxiv:2308.11432", "github.com/joaomdmoura/crewai"],
    },
    "python": {
        "summary": "Python is the dominant language for AI/ML with a rich ecosystem of libraries.",
        "key_facts": [
            "asyncio enables concurrent I/O without threads",
            "FastAPI is the fastest Python web framework for APIs",
            "Pydantic v2 uses Rust for 5-50x validation speedup",
            "uvloop replaces asyncio event loop for 2-4x throughput",
        ],
        "sources": ["docs.python.org", "fastapi.tiangolo.com"],
    },
    "orchestration": {
        "summary": "Orchestration coordinates multiple agents, manages state, and aggregates results.",
        "key_facts": [
            "Task decomposition is key to effective orchestration",
            "Confidence scoring enables dynamic agent selection",
            "Result aggregation requires semantic understanding",
            "Fault tolerance via fallback chains is critical",
        ],
        "sources": ["arxiv:2309.07864", "microsoft.com/semantic-kernel"],
    },
}

DEFAULT_RESPONSE = {
    "summary": "Research completed on the provided topic. Domain knowledge retrieved from internal knowledge base.",
    "key_facts": [
        "Topic identified and analyzed",
        "Related concepts mapped",
        "Confidence assessment performed",
        "Cross-references validated",
    ],
    "sources": ["internal-kb-v2", "domain-expert-synthesis"],
}


class ResearchAgent(BaseAgent):
    name = "research_agent"
    description = "Retrieves and synthesizes knowledge on any topic from structured knowledge bases."
    version = "1.0.0"
    capabilities = [
        "research",
        "search",
        "find",
        "information",
        "knowledge",
        "what is",
        "explain",
        "define",
        "history",
        "overview",
        "ai",
        "multi-agent",
        "python",
        "orchestration",
    ]

    async def run(self, input_data: AgentInput) -> AgentOutput:
        start = time.perf_counter()
        # Simulate async I/O (network/DB lookup)
        await asyncio.sleep(0.05)

        task_lower = input_data.task.lower()
        matched_key = next((k for k in KNOWLEDGE_BASE if k in task_lower), None)

        if matched_key:
            kb_entry = KNOWLEDGE_BASE[matched_key]
            result = {
                "topic": matched_key,
                "summary": kb_entry["summary"],
                "key_facts": kb_entry["key_facts"],
                "sources": kb_entry["sources"],
                "context_applied": bool(input_data.context),
            }
            confidence = 0.92
        else:
            result = {
                "topic": input_data.task[:60],
                **DEFAULT_RESPONSE,
                "context_applied": bool(input_data.context),
            }
            confidence = 0.65

        return self._make_output(input_data, result, confidence, start)
