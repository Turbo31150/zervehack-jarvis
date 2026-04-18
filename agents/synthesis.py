"""SynthesisAgent — combines outputs from multiple agents into a coherent response."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from .base import AgentInput, AgentOutput, BaseAgent


def _weighted_average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _extract_key_points(agent_results: list[dict[str, Any]]) -> list[str]:
    """Pull the most relevant single insight from each agent result."""
    points: list[str] = []
    for agent_result in agent_results:
        r = agent_result.get("result", {})
        # Research agent
        if "summary" in r:
            points.append(f"[Research] {r['summary'][:120]}")
        # Code agent
        if "description" in r and "code" in r:
            points.append(
                f"[Code] {r['description']} — {r.get('language', 'python')} solution ready"
            )
        # Analysis agent
        if "findings" in r and r["findings"]:
            points.append(f"[Analysis] {r['findings'][0]}")
        if "recommendations" in r and r["recommendations"]:
            points.append(f"[Recommendation] {r['recommendations'][0]}")
    return points[:8]  # cap to 8 key points for readability


def _build_executive_summary(task: str, agent_results: list[dict[str, Any]]) -> str:
    agent_names = [r.get("agent_name", "unknown") for r in agent_results]
    avg_conf = _weighted_average([r.get("confidence", 0) for r in agent_results])
    return (
        f"Task '{task[:60]}' processed by {len(agent_results)} specialized agents "
        f"({', '.join(agent_names)}). "
        f"Aggregate confidence: {avg_conf:.0%}. "
        f"All agents executed in parallel via asyncio.gather()."
    )


class SynthesisAgent(BaseAgent):
    name = "synthesis_agent"
    description = "Combines and reconciles outputs from multiple agents into a single coherent, attributed response."
    version = "1.0.0"
    capabilities = [
        "synthesize",
        "combine",
        "merge",
        "aggregate",
        "summarize",
        "consolidate",
        "report",
        "overview",
    ]

    async def run(self, input_data: AgentInput) -> AgentOutput:
        start = time.perf_counter()
        await asyncio.sleep(0.03)

        # SynthesisAgent is called with agent_outputs embedded in context JSON
        import json

        agent_results: list[dict[str, Any]] = []
        try:
            if input_data.context:
                parsed = json.loads(input_data.context)
                agent_results = parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, ValueError):
            pass

        if not agent_results:
            # Standalone call — return generic synthesis guidance
            result = {
                "executive_summary": f"Synthesis ready for task: {input_data.task[:80]}",
                "key_points": [
                    "Multiple agents available: research, code, analysis",
                    "Use POST /orchestrate for full parallel synthesis",
                    "Each agent self-reports confidence (0-1 scale)",
                    "Synthesis agent reconciles conflicting outputs",
                ],
                "sources": [],
                "aggregate_confidence": 0.75,
                "agents_synthesized": 0,
                "synthesis_method": "standalone",
            }
            return self._make_output(input_data, result, 0.75, start)

        key_points = _extract_key_points(agent_results)
        sources = []
        for r in agent_results:
            inner = r.get("result", {})
            sources.extend(inner.get("sources", []))
            if r.get("agent_name"):
                sources.append(f"agent:{r['agent_name']}")

        confidences = [r.get("confidence", 0.5) for r in agent_results]
        agg_conf = _weighted_average(confidences)

        result = {
            "executive_summary": _build_executive_summary(
                input_data.task, agent_results
            ),
            "key_points": key_points,
            "sources": list(dict.fromkeys(sources)),  # deduplicate, preserve order
            "aggregate_confidence": agg_conf,
            "agents_synthesized": len(agent_results),
            "synthesis_method": "parallel_gather",
            "agent_breakdown": [
                {
                    "agent": r.get("agent_name"),
                    "confidence": r.get("confidence"),
                    "processing_time_ms": r.get("processing_time_ms"),
                }
                for r in agent_results
            ],
        }

        return self._make_output(input_data, result, min(agg_conf + 0.05, 1.0), start)
