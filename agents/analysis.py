"""AnalysisAgent — analyzes tasks, data, and provides structured insights."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from .base import AgentInput, AgentOutput, BaseAgent

ANALYSIS_PATTERNS: dict[str, dict[str, Any]] = {
    "performance": {
        "dimensions": ["latency", "throughput", "resource_utilization", "scalability"],
        "findings": [
            "Parallel execution reduces end-to-end latency by 60-80% vs sequential",
            "asyncio.gather() achieves near-linear speedup for I/O-bound agents",
            "Pydantic v2 validation adds <1ms overhead per request",
            "Agent cold-start dominates first-request latency",
        ],
        "recommendations": [
            "Use connection pooling for external API calls",
            "Implement response caching with TTL for repeated queries",
            "Pre-warm agents at startup to eliminate cold-start penalty",
            "Apply circuit breakers for unreliable downstream services",
        ],
        "risk_level": "low",
        "confidence": 0.91,
    },
    "architecture": {
        "dimensions": [
            "modularity",
            "fault_tolerance",
            "extensibility",
            "observability",
        ],
        "findings": [
            "Orchestrator pattern cleanly separates routing from execution",
            "BaseAgent ABC enforces consistent interface across agents",
            "Pydantic models provide schema validation at boundaries",
            "Async-first design maximizes concurrency without thread overhead",
        ],
        "recommendations": [
            "Add distributed tracing (OpenTelemetry) for production observability",
            "Implement agent health checks with exponential backoff",
            "Use message queues (Redis Streams) for agent decoupling at scale",
            "Consider actor model (Ray) for stateful agents",
        ],
        "risk_level": "low",
        "confidence": 0.94,
    },
    "security": {
        "dimensions": [
            "authentication",
            "authorization",
            "input_validation",
            "rate_limiting",
        ],
        "findings": [
            "API endpoints currently lack authentication middleware",
            "Task inputs need sanitization before agent processing",
            "No rate limiting exposes endpoints to DoS risk",
            "Agent-to-agent communication is internal (low risk)",
        ],
        "recommendations": [
            "Add JWT/API key authentication via FastAPI dependencies",
            "Implement per-IP rate limiting with slowapi",
            "Validate and truncate task strings to prevent prompt injection",
            "Add request signing for agent-to-agent calls in production",
        ],
        "risk_level": "medium",
        "confidence": 0.88,
    },
    "cost": {
        "dimensions": ["compute", "memory", "api_costs", "operational"],
        "findings": [
            "Local agent execution eliminates external LLM API costs",
            "asyncio concurrency reduces instance count vs thread-per-request",
            "In-memory knowledge base avoids DB query costs",
            "Single-process deployment minimizes infrastructure overhead",
        ],
        "recommendations": [
            "Profile memory usage under load before production deployment",
            "Consider lazy-loading large knowledge bases to reduce startup RAM",
            "Implement request batching for bulk processing scenarios",
            "Monitor agent processing_time_ms to identify optimization targets",
        ],
        "risk_level": "low",
        "confidence": 0.85,
    },
}

DEFAULT_ANALYSIS = {
    "dimensions": ["feasibility", "complexity", "impact", "timeline"],
    "findings": [
        "Task is well-scoped and implementable with current architecture",
        "Complexity is moderate — manageable within MVP timeframe",
        "Multi-agent approach adds clear value through specialization",
        "Parallel execution pattern is applicable to this problem domain",
    ],
    "recommendations": [
        "Start with a working prototype, iterate based on real usage patterns",
        "Instrument early to collect baseline performance metrics",
        "Design agent interfaces before implementation to allow parallel work",
        "Validate outputs with domain experts before production rollout",
    ],
    "risk_level": "low",
    "confidence": 0.78,
}


class AnalysisAgent(BaseAgent):
    name = "analysis_agent"
    description = "Analyzes systems, data, and problems — provides structured insights, findings, and recommendations."
    version = "1.0.0"
    capabilities = [
        "analyze",
        "analysis",
        "evaluate",
        "assess",
        "review",
        "compare",
        "performance",
        "architecture",
        "security",
        "cost",
        "risk",
        "benchmark",
        "audit",
        "insight",
        "metrics",
    ]

    async def run(self, input_data: AgentInput) -> AgentOutput:
        start = time.perf_counter()
        await asyncio.sleep(0.06)

        task_lower = input_data.task.lower()
        matched_key = next((k for k in ANALYSIS_PATTERNS if k in task_lower), None)

        if matched_key:
            pattern = ANALYSIS_PATTERNS[matched_key]
            confidence = pattern["confidence"]
            result = {
                "subject": input_data.task[:80],
                "analysis_type": matched_key,
                "dimensions_evaluated": pattern["dimensions"],
                "findings": pattern["findings"],
                "recommendations": pattern["recommendations"],
                "risk_level": pattern["risk_level"],
                "context_applied": bool(input_data.context),
            }
        else:
            confidence = DEFAULT_ANALYSIS["confidence"]
            result = {
                "subject": input_data.task[:80],
                "analysis_type": "general",
                "dimensions_evaluated": DEFAULT_ANALYSIS["dimensions"],
                "findings": DEFAULT_ANALYSIS["findings"],
                "recommendations": DEFAULT_ANALYSIS["recommendations"],
                "risk_level": DEFAULT_ANALYSIS["risk_level"],
                "context_applied": bool(input_data.context),
            }

        return self._make_output(input_data, result, confidence, start)
