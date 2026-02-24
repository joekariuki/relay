# Relay

A multilingual AI support agent for mobile money services, built with Claude and OpenAI. Handles customer queries in English, French, and Swahili through text and voice, with a comprehensive evaluation framework for measuring agent reliability.

Relay simulates "DuniaWallet", a fictional mobile money service, with 8 demo accounts, transaction histories, fee structures, policies, and agent locations across Senegal, Mali, Cote d'Ivoire, and Burkina Faso.

## Features

- **Tool-use agent** — Claude Sonnet via Pydantic AI orchestrates 7 tools (balance checks, transactions, fees, agent lookup, policies, support tickets) through a multi-turn conversation loop
- **Multilingual support** — English, French, and Swahili with automatic language detection and code-switching handling (e.g. "Nataka ku-check balance yangu")
- **Voice pipeline** — Whisper ASR for speech-to-text, language-specific TTS voices (alloy/nova/echo), full latency tracking at every stage
- **Evaluation framework** — 100+ curated test cases scored across 4 dimensions: groundedness, hallucination detection, compliance, and language quality
- **Safety guardrails** — Prompt injection detection, PII flagging, account ID masking, and 10 explicit behavioral rules enforced via system prompt
- **Low-literacy handling** — SMS-style queries ("bal pls", "hw mch 2 snd 50k") and abbreviated inputs
- **Debug panel** — Collapsible UI showing tool calls, arguments, results, and latency breakdown for every response

## Architecture

### Text Pipeline

```
┌──────────┐     ┌────────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────┐
│  User    │────>│ Guardrails │────>│   Language     │────>│ Claude       │────>│ Response │
│  Message │     │ (regex)    │     │   Detection    │     │ Tool Loop    │     │          │
└──────────┘     └────────────┘     │ (Haiku/heur.) │     │ (max 5 rds)  │     └──────────┘
                  flags, doesn't     └───────────────┘     │              │
                  hard-block              │                │  ┌─────────┐ │
                                          ▼                │  │ 7 Tools │ │
                                   ┌─────────────┐        │  └─────────┘ │
                                   │ System      │───────>│  balance     │
                                   │ Prompt      │        │  txns        │
                                   │ (EN/FR/SW)  │        │  fees        │
                                   └─────────────┘        │  agents      │
                                                          │  policies    │
                                                          │  tickets     │
                                                          └──────────────┘
```

### Voice Pipeline

```
┌───────┐     ┌───────────┐     ┌─────────────────┐     ┌───────────┐     ┌───────┐
│ Audio │────>│ Whisper   │────>│ Agent Pipeline   │────>│ OpenAI    │────>│ Audio │
│ (webm)│     │ ASR       │     │ (same as above)  │     │ TTS       │     │ (mp3) │
└───────┘     │           │     └─────────────────┘     │           │     └───────┘
              │ transcript│                              │ voice per │
              │ language  │                              │ language: │
              │ asr_ms    │                              │ en: alloy │
              └───────────┘                              │ fr: nova  │
                                                         │ sw: echo  │
                                                         │ tts_ms    │
                                                         └───────────┘
```

### Evaluation Pipeline

```
┌────────────┐     ┌─────────────┐     ┌──────────────────────────────────┐     ┌────────┐
│ 100+ Test  │────>│ Agent       │────>│ Scoring (parallel per case)      │────>│ Report │
│ Cases      │     │ Pipeline    │     │                                  │     │        │
│            │     │ (semaphore  │     │  Groundedness  (LLM-as-judge)   │     │ scores │
│ 10 cats:   │     │  concur=5)  │     │  Hallucination (LLM-as-judge)   │     │ by cat │
│ balance    │     └─────────────┘     │  Compliance    (rule-based)      │     │ fails  │
│ txns       │                         │  Language      (LLM-as-judge)   │     └────────┘
│ fees       │                         │  Tool correct. (Jaccard)        │
│ disputes   │                         └──────────────────────────────────┘
│ FR / SW    │
│ code-switch│
│ safety     │
│ out-of-scope│
│ low-literacy│
└────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM framework | Pydantic AI (`pydantic-ai-slim`) — provider-agnostic Agent + tool decorators |
| Agent reasoning | Claude Sonnet via Pydantic AI Agent (tool-use loop, max 5 rounds) |
| Language detection | Claude Haiku via `model_request()` (with keyword heuristic fallback) |
| Eval judges | Claude Haiku via `model_request()` (groundedness, hallucination, language quality) |
| Speech-to-text | OpenAI Whisper (`whisper-1`) |
| Text-to-speech | OpenAI TTS (`tts-1`) |
| Backend | Python 3.11+, FastAPI, Pydantic, `mypy --strict` |
| Frontend | React 18, TypeScript (strict), Vite, Tailwind CSS |
| Testing | pytest (157 tests), pytest-asyncio |

## Project Structure

```
relay/
├── backend/
│   ├── src/
│   │   ├── config.py              # Environment config (pydantic-settings)
│   │   ├── agent/
│   │   │   ├── core.py            # Pydantic AI Agent with @tool decorators + orchestration
│   │   │   ├── tools.py           # 7 tool handler implementations
│   │   │   ├── prompts.py         # System prompts (EN/FR/SW, 10 rules each)
│   │   │   ├── router.py          # Language detection (Haiku + heuristic)
│   │   │   └── guardrails.py      # Injection & PII detection (flag, don't block)
│   │   ├── knowledge/
│   │   │   ├── accounts.py        # 8 demo accounts (Senegal, Mali, CI, BF)
│   │   │   ├── transactions.py    # ~80 transactions across accounts
│   │   │   ├── fees.py            # Fee rules by corridor
│   │   │   ├── policies.py        # 10 policy topics (EN/FR)
│   │   │   └── agents_data.py     # 18 cash-in/out agent locations
│   │   ├── eval/
│   │   │   ├── harness.py         # Async eval runner (bounded concurrency)
│   │   │   ├── test_cases.py      # 100+ curated test cases, 10 categories
│   │   │   ├── groundedness.py    # LLM-as-judge: claims vs tool results
│   │   │   ├── hallucination.py   # LLM-as-judge: fabricated data detection
│   │   │   ├── compliance.py      # Rule-based: no full IDs, no financial advice
│   │   │   └── language_quality.py # LLM-as-judge: language correctness
│   │   ├── voice/
│   │   │   └── pipeline.py        # Whisper ASR → Agent → TTS
│   │   └── api/
│   │       ├── server.py          # FastAPI endpoints
│   │       └── schemas.py         # Request/response validation
│   └── tests/                     # 157 unit tests
├── frontend/
│   └── src/
│       ├── App.tsx                # Main layout
│       ├── components/            # ChatWindow, DebugPanel, VoiceRecorder, etc.
│       └── hooks/                 # useChat, useVoice
└── docs/
    └── design-decisions.md        # Architecture rationale
```

## Quick Start

**Prerequisites:** Python 3.11+, Node.js 18+, [uv](https://docs.astral.sh/uv/)

```bash
# Clone
git clone https://github.com/your-username/relay.git
cd relay

# Backend
cd backend
uv venv && uv pip install -e ".[dev]"
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY (required) and OPENAI_API_KEY (for voice)

# Frontend
cd ../frontend
npm install
```

**Run both (two terminals):**

```bash
# Terminal 1 — Backend (port 8000)
cd backend && uv run uvicorn src.api.server:app --reload --port 8000

# Terminal 2 — Frontend (port 5173)
cd frontend && npm run dev
```

Open **http://localhost:5173** — the Vite dev server proxies `/api/*` requests to the backend.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check with version and environment |
| `POST` | `/chat` | Text message → agent response with tool calls and latency |
| `POST` | `/voice` | Audio upload (multipart) → ASR → agent → optional TTS |
| `POST` | `/eval` | Run evaluation suite (optional: `category`, `max_cases`) |

**Example:**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my balance?", "account_id": "acc_001"}'
```

## Running Evaluations

The eval framework runs test cases against the live agent and scores responses across multiple dimensions.

```bash
# Quick smoke test (5 cases, ~30 seconds)
curl -X POST http://localhost:8000/eval \
  -H "Content-Type: application/json" \
  -d '{"max_cases": 5}'

# Run a specific category
curl -X POST http://localhost:8000/eval \
  -H "Content-Type: application/json" \
  -d '{"category": "balance_inquiry", "max_cases": 10}'

# Full suite (100+ cases — takes several minutes, costs ~$2-4 in API calls)
curl -X POST http://localhost:8000/eval \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Scoring dimensions:**

| Dimension | Method | What it measures |
|-----------|--------|-----------------|
| Tool correctness | Jaccard similarity | Did the agent call the right tools? |
| Groundedness | LLM-as-judge (Haiku) | Are claims supported by tool results? |
| Hallucination | LLM-as-judge (Haiku) | Did the agent fabricate data, policies, or reassurances? |
| Compliance | Rule-based regex | Are account IDs masked? No financial advice given? |
| Language quality | LLM-as-judge (Haiku) | Correct language, fluent, no code-switching errors? |

## Agent Tools

| Tool | Description |
|------|-------------|
| `check_balance` | Account balance, holder name, KYC tier (account IDs masked in response) |
| `get_transactions` | Recent transactions with type, amount, status (default 5, max 20) |
| `lookup_transaction` | Search by transaction ID, recipient name, or keyword |
| `calculate_fees` | Fee for amount and corridor (domestic, SN-ML, SN-CI, SN-BF) |
| `find_agent` | Nearby cash-in/out agent locations by city or neighborhood |
| `get_policy` | Service policies by topic, with keyword search fallback |
| `create_support_ticket` | Escalate to human support with category and priority |

## Supported Languages

| Language | Detection | Voice | Test Coverage |
|----------|-----------|-------|---------------|
| English | Haiku + heuristic | alloy | 15+ balance, txn, fee cases |
| French | Haiku + keyword markers | nova | 15 dedicated FR cases + bilingual policies |
| Swahili | Haiku + keyword markers | echo | 15 dedicated SW cases + low-literacy variants |

Code-switching (e.g. "Nataka ku-check balance yangu") is detected and handled — the agent responds in the dominant language.

## Testing

```bash
cd backend

# Unit tests (157 tests, no API keys needed)
uv run pytest tests/ -v

# Type checking (strict mode, 29 source files)
uv run mypy src/ --strict

# Frontend build
cd ../frontend && npm run build
```

## Design Decisions

Key architectural choices are documented in [docs/design-decisions.md](docs/design-decisions.md):

- **Pydantic AI** over direct Anthropic SDK — provider-agnostic model swapping, auto-generated tool schemas from type hints, `@agent.tool` decorators replace ~170 lines of manual JSON schema
- **Pydantic AI** over LangChain/LangGraph — lightweight, Pydantic-native, slim dependency footprint, transparent tool-use loop via `usage_limits`
- **REST API** over GraphQL — small API surface (4 endpoints), simpler for file uploads
- **Custom eval framework** over Promptfoo — domain-specific scoring (financial hallucinations, ID masking), tighter integration with agent pipeline
- **In-memory data** over database — zero infrastructure, deterministic tests, instant startup

## What I'd Build at Scale

This project is a demo. Here's what a production system handling 10M+ interactions/month would need:

**Infrastructure:** PostgreSQL/CockroachDB for accounts and transactions, Redis for session state and rate limiting, async task queue (Celery/Temporal) for eval runs, structured observability with OpenTelemetry, Kubernetes for horizontal scaling.

**Agent improvements:** Conversation memory across sessions, streaming responses (SSE) for lower perceived latency, A/B testing framework for prompt variants, retrieval-augmented generation (RAG) over a real policy knowledge base instead of hardcoded documents, fine-tuned language detection for low-resource languages.

**Voice at scale:** Real-time streaming ASR (WebSocket-based) instead of batch transcription, voice activity detection to trim silence, latency budgets per pipeline stage with SLOs, fallback TTS engines for reliability, on-device wake word detection for mobile.

**Evaluation in CI:** Nightly eval runs against the full suite with regression alerts, cost tracking per eval run, human-in-the-loop review for edge cases the automated judges can't resolve, shadow mode to compare new model versions against production before rollout.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
