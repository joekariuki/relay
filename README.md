# Relay

A multilingual AI support agent for mobile money services, built with Claude and OpenAI. Handles customer queries in English, French, and Swahili through text and voice, with multi-agent routing, RAG-powered policy retrieval, and a comprehensive evaluation framework for measuring agent reliability.

Relay simulates "DuniaWallet", a fictional pan-African mobile money service, with 17 demo accounts across 12 countries, 10 currencies, transaction histories, 30+ fee corridors with FX conversion, policies, and 38+ agent locations spanning West, East, North, and Southern Africa plus UK and US diaspora corridors.

## Features

- **Multi-agent routing** — Intent classifier (Haiku) routes queries to support, fraud, or escalation specialist agents, each with tailored tools and system prompts
- **Tool-use agent** — Claude Sonnet via Pydantic AI orchestrates 8 tools (balance checks, transactions, fees, FX rates, agent lookup, policies, support tickets) through a multi-turn conversation loop
- **Multi-currency support** — 10 currencies (XOF, NGN, GHS, KES, TZS, ZAR, MAD, EGP, GBP, USD) with FX conversion, rate display, and currency-aware formatting
- **Pan-African coverage** — 12 countries, 17 demo accounts, 38+ agent locations, 30+ fee corridors including diaspora remittance (UK/US to Africa)
- **RAG policy retrieval** — ChromaDB vector store with OpenAI embeddings for semantic policy search, with keyword fallback chain
- **Conversation memory** — Session-based history using pydantic-ai's native `message_history` with in-memory or PostgreSQL store, TTL expiry, and automatic history pruning
- **Streaming responses** — Server-Sent Events (SSE) via pydantic-ai's `run_stream()` deliver tokens progressively for real-time chat UX
- **Multilingual support** — English, French, and Swahili with automatic language detection and code-switching handling (e.g. "Nataka ku-check balance yangu")
- **Voice pipeline** — Whisper ASR for speech-to-text, language-specific TTS voices (alloy/nova/echo), full latency tracking at every stage
- **Real-time voice mode** — WebSocket-based live voice conversation with Deepgram Nova-2 streaming ASR, built-in VAD, sentence-level OpenAI TTS streaming, and shared conversation context with text chat
- **Evaluation framework** — 155+ curated test cases scored across 5 dimensions (groundedness, hallucination, compliance, language quality, tool correctness) with CI eval gates via GitHub Actions
- **PostgreSQL persistence** — Optional async session storage via asyncpg with auto-migration, feature-flagged with in-memory fallback
- **Safety guardrails** — Prompt injection detection, PII flagging, account ID masking, and 10 explicit behavioral rules enforced via system prompt
- **Low-literacy handling** — SMS-style queries ("bal pls", "hw mch 2 snd 50k") and abbreviated inputs
- **Debug panel** — Collapsible UI showing tool calls, arguments, results, and latency breakdown for every response

## Architecture

### Text Pipeline

```
┌──────────┐     ┌────────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────┐
│  User    │────>│ Guardrails │────>│   Language     │────>│ Claude       │─SSE>│ Response │
│  Message │     │ (regex)    │     │   Detection    │     │ Tool Loop    │     │ (stream) │
└──────────┘     └────────────┘     │ (Haiku/heur.) │     │ (max 5 rds)  │     └──────────┘
                  flags, doesn't     └───────────────┘     │              │
                  hard-block              │                │  ┌─────────┐ │
                                          ▼                │  │ 8 Tools │ │
                                   ┌─────────────┐        │  └─────────┘ │
                                   │ System      │───────>│  balance     │
                                   │ Prompt      │        │  txns        │
                                   │ (EN/FR/SW)  │        │  fees        │
                                   └─────────────┘        │  FX rates    │
                                                          │  agents      │
                                                          │  policies    │
                                                          │  tickets     │
                                                          └──────────────┘
```

### Voice Pipeline (Batch)

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

### Real-Time Voice Pipeline (WebSocket)

```
┌──────────┐  PCM   ┌───────────┐ partials ┌────────────┐ text  ┌───────────┐ mp3 chunks ┌──────────┐
│ Browser  │──────>│ Deepgram  │────────>│ Agent       │─────>│ OpenAI    │──────────>│ Browser  │
│ AudioWklt│  16kHz │ Nova-2    │  final  │ Pipeline    │      │ TTS       │           │ Playback │
│ Capture  │  mono  │ (stream)  │────────>│ (stream_    │      │ (sentence │           │ Queue    │
└──────────┘       │ +VAD      │         │  agent_     │      │  by       │           └──────────┘
     ▲              └───────────┘         │  response)  │      │  sentence)│
     │                                    └────────────┘      └───────────┘
     │                                          │
     └──── WebSocket (/ws/voice) ──────────────┘
```

### Evaluation Pipeline

```
┌────────────┐     ┌─────────────┐     ┌──────────────────────────────────┐     ┌────────┐
│ 155+ Test  │────>│ Agent       │────>│ Scoring (parallel per case)      │────>│ Report │
│ Cases      │     │ Pipeline    │     │                                  │     │        │
│            │     │ (semaphore  │     │  Groundedness  (LLM-as-judge)   │     │ scores │
│ 16 cats:   │     │  concur=5)  │     │  Hallucination (LLM-as-judge)   │     │ by cat │
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
| Streaming ASR | Deepgram Nova-2 (real-time WebSocket transcription) |
| RAG / Embeddings | ChromaDB (in-memory) + OpenAI `text-embedding-3-small` |
| Database (optional) | PostgreSQL via asyncpg, feature-flagged |
| CI/CD | GitHub Actions eval pipeline with threshold gates |
| Testing | pytest (370 tests), pytest-asyncio |

## Project Structure

```
relay/
├── .github/
│   └── workflows/
│       └── eval.yml               # CI eval pipeline (20 critical cases per PR)
├── backend/
│   ├── src/
│   │   ├── config.py              # Environment config (pydantic-settings)
│   │   ├── session.py             # In-memory session store with TTL
│   │   ├── agent/
│   │   │   ├── core.py            # Pydantic AI Agent orchestration + streaming
│   │   │   ├── orchestrator.py    # Multi-agent intent classification + routing
│   │   │   ├── tools.py           # 8 tool handler implementations
│   │   │   ├── prompts.py         # System prompts (EN/FR/SW, 10 rules each)
│   │   │   ├── router.py          # Language detection (Haiku + heuristic)
│   │   │   └── guardrails.py      # Injection & PII detection (flag, don't block)
│   │   ├── knowledge/
│   │   │   ├── accounts.py        # 17 demo accounts (12 countries, 10 currencies)
│   │   │   ├── transactions.py    # ~120 transactions across accounts
│   │   │   ├── fees.py            # Fee rules for 30+ corridors with FX conversion
│   │   │   ├── policies.py        # 12 policy topics (EN/FR)
│   │   │   ├── agents_data.py     # 38+ agent locations across 12 countries
│   │   │   └── rag.py             # ChromaDB embedding + semantic policy retrieval
│   │   ├── db/
│   │   │   ├── connection.py      # asyncpg pool management + health checks
│   │   │   ├── session_store.py   # PostgreSQL-backed session store
│   │   │   └── migrations/        # SQL migration scripts
│   │   ├── eval/
│   │   │   ├── harness.py         # Async eval runner (bounded concurrency)
│   │   │   ├── test_cases.py      # 155+ curated test cases, 16 categories
│   │   │   ├── ci_subset.py       # 20 critical CI case IDs + thresholds
│   │   │   ├── run_ci_eval.py     # CLI runner for CI eval pipeline
│   │   │   ├── groundedness.py    # LLM-as-judge: claims vs tool results
│   │   │   ├── hallucination.py   # LLM-as-judge: fabricated data detection
│   │   │   ├── compliance.py      # Rule-based: no full IDs, no financial advice
│   │   │   └── language_quality.py # LLM-as-judge: language correctness
│   │   ├── voice/
│   │   │   ├── pipeline.py        # Whisper ASR → Agent → TTS (batch)
│   │   │   └── realtime.py        # Deepgram streaming ASR → Agent → TTS (WebSocket)
│   │   └── api/
│   │       ├── server.py          # FastAPI endpoints + /ws/voice WebSocket
│   │       └── schemas.py         # Request/response/WebSocket message schemas
│   └── tests/                     # 370 unit tests
├── frontend/
│   └── src/
│       ├── App.tsx                # Main layout + voice mode integration
│       ├── audio/                 # AudioWorklet PCM capture processor
│       ├── components/            # ChatWindow, DebugPanel, VoiceRecorder, VoiceModeOverlay
│       └── hooks/                 # useChat, useVoice, useVoiceMode
└── docs/
    └── design-decisions.md        # Architecture rationale
```

## Quick Start

**Prerequisites:** Python 3.11+, Node.js 18+, [uv](https://docs.astral.sh/uv/)

```bash
# Clone
git clone https://github.com/joekariuki/relay.git
cd relay

# Backend
cd backend
uv venv && uv pip install -e ".[dev]"
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY (required), OPENAI_API_KEY (for voice/TTS),
# and optionally DEEPGRAM_API_KEY (for real-time voice mode)

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
| `GET` | `/health` | Health check with version, environment, and PostgreSQL status |
| `GET` | `/accounts` | List all demo accounts grouped by region |
| `POST` | `/chat` | Text message → agent response with tool calls and latency |
| `POST` | `/chat/stream` | SSE streaming — tokens delivered progressively via `text_delta` events |
| `POST` | `/voice` | Audio upload (multipart) → ASR → agent → optional TTS |
| `WS` | `/ws/voice` | Real-time voice mode — bidirectional audio/transcript/agent streaming |
| `DELETE` | `/sessions/{id}` | Delete a conversation session |
| `POST` | `/eval` | Run evaluation suite (optional: `category`, `max_cases`) |

**Example:**

```bash
# First message (auto-creates a session)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my balance?", "account_id": "acc_001"}'
# Response includes session_id — pass it back for multi-turn conversations

# Follow-up with conversation context
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the fee to send half of that to Mali?", "account_id": "acc_001", "session_id": "<session_id>"}'
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

# Full suite (155+ cases — takes several minutes, costs ~$2-4 in API calls)
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
| `calculate_fees` | Fee for amount and corridor (domestic per country, 30+ cross-border and international corridors) with FX rate display |
| `get_exchange_rate` | FX rate between any two supported currencies with spread |
| `find_agent` | Nearby cash-in/out agent locations by city or neighborhood across 12 countries |
| `get_policy` | Service policies by topic, with RAG semantic search and keyword fallback |
| `create_support_ticket` | Escalate to human support with category and priority |

## Conversation Memory

The agent maintains context across turns within a session. When a user asks "What was that number again?" after a balance check, the agent recalls the balance without making another tool call.

**How it works:**

- Each conversation is assigned a `session_id` (auto-generated on first request, returned in every response)
- Message history is stored server-side using pydantic-ai's native `ModelMessage` format (in-memory by default, or PostgreSQL when `USE_POSTGRES=true`)
- On each request, the full conversation history is loaded and passed to `Agent.run()` / `Agent.iter()` via the `message_history` parameter
- After the agent responds, the updated history (including the new exchange) is persisted back to the store
- Sessions expire after 30 minutes of inactivity (configurable via `SESSION_TTL_MINUTES`)
- A `history_processors` cap prevents unbounded token growth by keeping only the most recent N message pairs (configurable via `SESSION_MAX_HISTORY`, default 20)

**Session lifecycle:**

1. **Create** — Automatic on first `/chat` or `/chat/stream` request without a `session_id`
2. **Continue** — Pass the returned `session_id` in subsequent requests
3. **Clear** — `DELETE /sessions/{session_id}` (frontend does this on "Clear chat" or account switch)
4. **Expire** — Automatic cleanup after TTL

**PostgreSQL persistence (optional):** Set `USE_POSTGRES=true` and `DATABASE_URL` to persist sessions to PostgreSQL via asyncpg. The PostgreSQL store implements the same interface as the in-memory store with atomic operations (UPDATE...RETURNING to prevent TOCTOU races) and auto-migration on startup. Falls back to in-memory when disabled.

## Voice Mode

Voice mode provides a real-time, call-like conversation with the agent. Instead of recording and sending audio in batches, users enter a persistent voice session where they speak naturally and hear the agent respond.

**How it works:**

1. User clicks the phone icon to enter voice mode
2. A WebSocket connection opens to `/ws/voice`, establishing a Deepgram streaming ASR connection
3. Microphone audio is captured via an AudioWorklet (16kHz mono PCM) and streamed to the backend in real-time
4. Deepgram provides interim transcripts (displayed live) and triggers utterance-end via built-in VAD (800ms silence threshold)
5. On utterance end, the agent processes the final transcript through the same pipeline as text chat
6. The agent response is synthesized sentence-by-sentence via OpenAI TTS and streamed back as MP3 audio chunks
7. Audio plays sequentially — the first sentence plays while subsequent sentences are still synthesizing

**Session integration:** Voice mode shares conversation context with text chat via `session_id`. A user can type a question, switch to voice mode, and say "What was that number again?" — the agent has the full history.

**Requirements:** A Deepgram API key (`DEEPGRAM_API_KEY` in `.env`) is required for voice mode. Sign up at [console.deepgram.com](https://console.deepgram.com) for a free tier with $200 in credits.

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

# Unit tests (370 tests, no API keys needed)
uv run pytest tests/ -v

# Type checking (strict mode)
uv run mypy src/ --strict

# Frontend build
cd ../frontend && npm run build
```

## Design Decisions

Key architectural choices are documented in [docs/design-decisions.md](docs/design-decisions.md):

- **Pydantic AI** over direct Anthropic SDK — provider-agnostic model swapping, auto-generated tool schemas from type hints, `@agent.tool` decorators replace ~170 lines of manual JSON schema
- **Pydantic AI** over LangChain/LangGraph — lightweight, Pydantic-native, slim dependency footprint, transparent tool-use loop via `usage_limits`
- **REST API** over GraphQL — small API surface (5 endpoints), simpler for file uploads
- **Custom eval framework** over Promptfoo — domain-specific scoring (financial hallucinations, ID masking), tighter integration with agent pipeline
- **In-memory data** over database — zero infrastructure, deterministic tests, instant startup (PostgreSQL available as opt-in for session persistence)
- **ChromaDB in-memory** over hosted vector DB — zero infrastructure for demo, embeddings rebuilt on startup from policy documents
- **Multi-agent via pydantic-ai** over LangGraph — lightweight routing with Haiku classifier, each specialist gets a tool subset, no framework overhead

## What I'd Build at Scale

This project is a demo with several production-grade patterns already implemented. Here's what's built and what a system handling 10M+ interactions/month would additionally need:

**Already built:** PostgreSQL session persistence (feature-flagged), RAG over policy documents (ChromaDB + OpenAI embeddings), multi-agent routing (support/fraud/escalation specialists), CI eval pipeline (GitHub Actions with threshold gates on every PR), multi-currency FX conversion across 30+ corridors.

**Infrastructure at scale:** CockroachDB for distributed accounts and transactions, Redis for session state and rate limiting, async task queue (Celery/Temporal) for eval runs, structured observability with OpenTelemetry, Kubernetes for horizontal scaling.

**Agent improvements:** A/B testing framework for prompt variants, fine-tuned local language detection for low-resource languages (replacing Haiku API calls), persistent vector store for RAG (replacing in-memory ChromaDB).

**Voice at scale:** Multi-region Deepgram endpoints for latency optimization, fallback TTS engines for reliability, on-device wake word detection for mobile, WebRTC for peer-to-peer audio with TURN server fallback, latency budgets per pipeline stage with SLOs.

**Evaluation at scale:** Nightly eval runs against the full suite with drift detection and regression alerts, cost tracking per eval run, human-in-the-loop review for edge cases the automated judges can't resolve, shadow mode to compare new model versions against production before rollout.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
