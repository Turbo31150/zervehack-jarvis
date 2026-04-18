# JARVIS-ZERO: Build Anything with Local AI Agents

> ZerveHack 2026 — $10,000 AI Hackathon | "Stop thinking, build it"

Turn any idea into a running multi-agent system in seconds. No cloud. No API keys. No limits.

---

## Architecture

```
POST /orchestrate  (or quick: POST /build?task=...)
         │
         ▼
OrchestratorAgent
  ├─ Scores task relevance per agent (0-1 confidence)
  ├─ Selects top agents (min 2 guaranteed)
  │
  └─ asyncio.gather() ──► ResearchAgent  ─┐
                      ──► CodeAgent      ─┼─► SynthesisAgent ──► Response
                      ──► AnalysisAgent  ─┘
                              │
                    [optional] Local LLM augmentation
                    (Ollama gemma3:4b / LM Studio qwen3.5)
```

### Agents

| Agent | Role |
|---|---|
| **OrchestratorAgent** | Task classification, parallel delegation |
| **ResearchAgent** | Knowledge retrieval, fact synthesis |
| **CodeAgent** | Code generation, algorithm selection |
| **AnalysisAgent** | Insight extraction, risk assessment |
| **SynthesisAgent** | Output aggregation, executive summary |

---

## Quickstart

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

## Usage

### Quick build (one-liner)

```bash
curl -X POST "http://localhost:8000/build?task=create+a+REST+API+for+inventory+management&use_llm=true"
```

### Full orchestration

```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"task": "build a real-time dashboard for GPU cluster monitoring", "use_llm": true}'
```

### Direct agent calls

```bash
curl -X POST http://localhost:8000/agent/code \
  -H "Content-Type: application/json" \
  -d '{"task": "write a Python async web scraper"}'
```

---

## Local LLM Backends (no cloud required)

| Backend | Endpoint | Model |
|---|---|---|
| LM Studio (M1) | `192.168.1.85:1234` | qwen3.5-9b |
| Ollama (local) | `127.0.0.1:11434` | gemma3:4b |

Auto-fallback: if the first backend is down, the system tries the next one transparently.

---

## Key Features

- **Parallel execution** — all agents run via `asyncio.gather()`, never sequentially
- **Local-first LLM** — augment any task with Ollama or LM Studio, zero cloud dependency
- **Confidence scoring** — each agent scores its own relevance; orchestrator selects top performers
- **One-liner `/build` endpoint** — paste any idea as a URL query param, get structured output instantly
- **Auto-failover** — LLM backends cascade automatically on failure

---

## Example Response

```json
{
  "request_id": "a1b2c3d4-...",
  "task": "build a real-time dashboard for GPU cluster monitoring",
  "total_agents_invoked": 3,
  "total_time_ms": 92.1,
  "llm_insight": "Start with a WebSocket endpoint exposing GPU metrics, then build a minimal React dashboard consuming it. Ship in under 2 hours.",
  "synthesis": { ... },
  "agent_outputs": [ ... ]
}
```

---

## Tech Stack

- **FastAPI** + **asyncio** — async parallel agent execution
- **Pydantic v2** — strict input/output validation
- **httpx** — async local LLM calls
- **Ollama** / **LM Studio** — local inference, no cloud
- **Python 3.11+**

---

Built in < 48h for ZerveHack. Theme: "Stop thinking, build it."
