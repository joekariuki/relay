# Design Decisions

This document captures key architectural and technical decisions made during the development of Relay, along with the reasoning behind each choice.

---

## 1. Direct SDK Usage vs. LLM Frameworks (LangChain / LangGraph)

**Decision**: Use the Anthropic Python SDK and OpenAI Python SDK directly instead of frameworks like LangChain or LangGraph. *(Update: the Anthropic SDK has since been replaced by Pydantic AI — see Decision #6.)*

**Context**: LangChain and LangGraph are popular frameworks that provide abstractions over LLM APIs, including tool-use orchestration, chain composition, and agent patterns. The question was whether to adopt one of these frameworks or build the agent loop directly against the vendor SDKs.

**Reasoning**:

- **Transparency of the tool-use loop**: The core agent in `src/agent/core.py` implements a tool-use loop in ~80 lines of clear, readable Python. Every step — guardrails, language detection, prompt selection, the Claude message loop with tool calls, response extraction — is explicit and easy to follow. A reviewer can read the code and immediately understand the full pipeline without needing to know framework internals.

- **Claude's native tool-use API is first-class**: Anthropic's SDK supports tool-use natively via `tools` and `tool_choice` parameters on `client.messages.create()`. The SDK handles the message/tool-result turn structure directly. There is no gap that a framework needs to bridge.

- **Minimal abstraction surface**: LangChain introduces its own abstractions (Chains, Agents, Tools, Memory, Callbacks) that add layers between the code and the actual API calls. For a focused demo project, these layers add complexity without proportional benefit. Direct SDK usage means fewer dependencies, fewer failure modes, and a smaller debugging surface.

- **Eval framework independence**: The evaluation harness (`src/eval/`) needs fine-grained control over how agent responses are scored — calling separate LLM-as-judge prompts for groundedness, hallucination detection, compliance, and language quality. Direct SDK calls give full control over model selection (Haiku for judges, Sonnet for the agent), prompt formatting, and result parsing without fighting framework conventions.

- **Portfolio signal**: For an Applied AI Engineer role, demonstrating understanding of the underlying APIs and building a clean orchestration loop from scratch is a stronger signal than wiring together framework components.

- **Dependency footprint**: The Anthropic SDK (`anthropic`) and OpenAI SDK (`openai`) are lightweight, well-maintained, and have stable APIs. LangChain has a large transitive dependency tree and undergoes frequent breaking changes.

**Trade-offs accepted**:

- We implement our own tool-use loop (message → tool_call → tool_result → message) rather than using a pre-built agent executor. This is straightforward with Claude's API but requires ~30 lines of loop logic.
- We don't get LangChain's built-in tracing/observability (LangSmith). Instead, we track latency manually with `time.perf_counter()` at each pipeline stage and include it in every response.
- If the project needed complex multi-agent workflows (handoffs, parallel agent execution, state machines), LangGraph would be worth reconsidering.

**Where each SDK is used** *(updated after Pydantic AI migration — see Decision #6)*:

| SDK | Module | Purpose |
|-----|--------|---------|
| `pydantic_ai.Agent` | `src/agent/core.py` | Main agent loop (Claude Sonnet, tool-use via `@agent.tool`) |
| `pydantic_ai.direct.model_request` | `src/agent/router.py` | Language detection (Claude Haiku) |
| `pydantic_ai.direct.model_request` | `src/eval/groundedness.py` | LLM-as-judge groundedness scoring |
| `pydantic_ai.direct.model_request` | `src/eval/hallucination.py` | LLM-as-judge hallucination detection |
| `pydantic_ai.direct.model_request` | `src/eval/language_quality.py` | LLM-as-judge language quality |
| `openai.AsyncOpenAI` | `src/voice/pipeline.py` | Whisper ASR + TTS synthesis |

---

## 2. REST API vs. GraphQL

**Decision**: Use a REST API with FastAPI instead of adding a GraphQL layer.

**Context**: The question was raised whether to add a GraphQL API layer alongside or instead of the REST endpoints.

**Reasoning**:

- **Scope discipline**: The API surface is small (4 endpoints: `/health`, `/chat`, `/voice`, `/eval`). GraphQL's query flexibility adds value when clients need to fetch varying subsets of deeply nested data across many entities. Our endpoints each return a single, well-defined response shape.

- **Voice endpoint incompatibility**: The `/voice` endpoint accepts `multipart/form-data` (audio file upload). GraphQL's standard transport (JSON over POST) doesn't naturally handle file uploads without additional libraries (e.g., `graphql-upload`), adding complexity for no benefit.

- **Demo clarity**: A hiring manager reviewing the project can immediately understand `POST /chat` with a JSON body. GraphQL adds a learning curve for reviewers unfamiliar with it and obscures the simplicity of the API.

- **FastAPI's strengths**: FastAPI provides automatic OpenAPI documentation, Pydantic validation, and async support out of the box. These cover the same developer-experience benefits that GraphQL's type system and introspection provide, without the overhead.

**When GraphQL would make sense**: If Relay evolved into a production system with a complex data model (accounts, transactions, tickets, agents) where the frontend needed flexible querying, GraphQL would be worth adding.

---

## 3. In-Memory Simulated Data vs. Database

**Decision**: Use in-memory Python data structures for all simulated account, transaction, and policy data.

**Context**: The project simulates a mobile money service ("DuniaWallet") with accounts, transactions, fees, policies, and agent locations.

**Reasoning**:

- **Demo focus**: The project is a portfolio piece demonstrating AI agent capabilities, not a production fintech system. The data layer exists to give the agent realistic tool results to work with.

- **Zero infrastructure**: No database setup, no migrations, no connection management. The project runs with `uv run uvicorn` and nothing else.

- **Deterministic testing**: In-memory data makes tests fast, deterministic, and require no fixtures or cleanup. Every test run starts from the same known state.

- **Instant startup**: No database connection delays. The server starts in milliseconds.

**Trade-offs accepted**: Data doesn't persist across restarts (irrelevant for a demo). Can't demonstrate database query optimization or ORM usage.

---

## 4. Evaluation: Custom Framework vs. Promptfoo

**Decision**: Build a custom evaluation framework instead of integrating Promptfoo or similar tools.

**Context**: Promptfoo is a popular open-source tool for testing LLM prompts and outputs with configurable assertions, grading, and reporting.

**Reasoning**:

- **Evaluation is the differentiator**: For Wave's Applied AI Engineer role, the eval framework is arguably the most important technical artifact. Building it from scratch demonstrates deep understanding of LLM evaluation challenges: groundedness verification, hallucination detection, compliance checking, and multilingual quality assessment.

- **Domain-specific scoring**: Our eval dimensions are tailored to mobile money support:
  - **Groundedness**: Does the agent's response match what the tools actually returned? (Critical for financial data)
  - **Hallucination detection**: Did the agent fabricate balances, fees, or transaction IDs?
  - **Compliance**: Are full account IDs or phone numbers exposed? Did the agent give financial advice?
  - **Language quality**: Is the response in the correct language with proper fluency?

  These scoring functions require domain knowledge that a generic tool wouldn't provide out of the box.

- **Full control over the judge prompts**: The LLM-as-judge prompts in `groundedness.py`, `hallucination.py`, and `language_quality.py` are carefully engineered for mobile money scenarios. With Promptfoo, we'd be constrained by its assertion types or would need to write custom graders anyway.

- **Integrated pipeline**: The eval harness runs the full agent pipeline (guardrails → language detection → tool-use loop → response) per test case, then scores all dimensions in parallel. This tight integration with the agent code would be harder to achieve through an external tool.

**When Promptfoo would make sense**: For ongoing prompt regression testing in a production system with CI/CD integration, Promptfoo's YAML-based test definitions and built-in CI support would reduce maintenance burden.

---

## 5. Per-Language Voice Selection

**Decision**: Map each supported language to a specific OpenAI TTS voice.

**Mapping**:
| Language | Voice | Rationale |
|----------|-------|-----------|
| English | `alloy` | Neutral, clear, professional |
| French | `nova` | Warm tone suited to French phonetics |
| Swahili | `echo` | Distinct voice for clear differentiation |

**Context**: OpenAI's TTS API offers multiple voice options. The question was whether to use a single voice for all languages or select per-language.

**Reasoning**: Different voices handle different languages' phonetic patterns with varying quality. Using distinct voices also provides an audio cue to the user about which language the system is responding in, improving the multilingual experience.

---

## 6. Pydantic AI vs. Direct Anthropic SDK

**Decision**: Replace all direct `anthropic.AsyncAnthropic` usage with [Pydantic AI](https://ai.pydantic.dev/) (`pydantic-ai-slim`), using `Agent` with `@agent.tool` decorators for the core agent and `model_request()` for lightweight LLM-as-judge calls.

**Context**: The original architecture (Decision #1) used the Anthropic SDK directly with a manual tool-use loop. As the project matured and the roadmap called for streaming responses, multi-agent handoff, and model experimentation (e.g., comparing Claude vs. GPT-4.1), the cost of maintaining provider-specific code increased. The question was whether to adopt a framework now or continue with direct SDK usage.

**Why now**:

- **Provider-agnostic model swapping**: Upcoming features require comparing model performance across providers (Anthropic, OpenAI). Pydantic AI lets you swap models by changing a config string (e.g., `"anthropic:claude-sonnet-4-5-20250929"` → `"openai:gpt-4.1"`). Without it, every provider would need its own client setup, message format handling, and tool schema translation.
- **Streaming and multi-agent handoff**: The next phases of the roadmap (SSE streaming, agent-to-agent handoff) are substantially easier to build on a framework that already handles the tool-use loop and provides streaming primitives.
- **Tool schema maintenance burden**: The manual `TOOL_DEFINITIONS` list was ~170 lines of JSON schema dicts that had to be kept in sync with the handler functions. Any parameter rename or type change required updating both places.

**Why Pydantic AI specifically**:

- **Already in the Pydantic ecosystem**: The project uses Pydantic everywhere — FastAPI request/response models, `pydantic-settings` for configuration, dataclass-style domain models. Pydantic AI is a natural extension.
- **`@agent.tool` auto-generates schemas from type hints**: Adding a tool is now a single decorated async function. The tool name, description (from docstring), and parameter schema (from type annotations) are all inferred automatically. This eliminated ~170 lines of manual JSON schema.
- **Two API surfaces for different needs**: `Agent` with `@agent.tool` for the core conversational agent (handles the full tool-use loop), and `model_request()` for simple one-shot LLM calls (eval scorers, language detection). Both use the same model string format.
- **Slim install**: `pydantic-ai-slim[anthropic,openai]` pulls in only what's needed — no heavy transitive dependencies.
- **`RunContext` dependency injection**: Tools receive runtime context (account ID, language, tool records) via `RunContext[AgentDeps]` without global state or closures.

**What changed vs. Decision #1**:

The original direct-SDK approach was the right call for the initial build — it kept the system transparent and dependency-light while the focus was on getting the agent pipeline working correctly. Pydantic AI preserves that transparency (the tool-use loop is still visible via `usage_limits`, tool functions are plain Python, prompt construction is explicit) while adding the provider abstraction needed for the next phase. The core pipeline structure (guardrails → language detection → prompt selection → agent → response) is unchanged.

**Trade-offs accepted**:

- **Framework dependency**: Adds `pydantic-ai-slim` as a dependency. However, it's maintained by the Pydantic team (same maintainers as FastAPI's validation layer) and has a stable API.
- **Tool-use loop is framework-managed**: The manual `while` loop in `_run_tool_loop()` is replaced by `agent.run()`. The loop is now less visible but controllable via `UsageLimits(request_limit=N)` and fully logged by Pydantic AI's instrumentation.
- **Provider SDK becomes transitive**: `anthropic` is no longer a direct dependency — it's pulled in via `pydantic-ai-slim[anthropic]`. This is fine for our use case but means provider SDK versions are managed by Pydantic AI.

**Migration scope** (8 atomic commits):

| What | Before | After |
|------|--------|-------|
| Core agent | `client.messages.create()` in a `while` loop | `Agent.run()` with `@agent.tool` decorators |
| Tool schemas | 170-line `TOOL_DEFINITIONS` list | Auto-generated from type hints and docstrings |
| Eval scorers | `client.messages.create()` with `client` param | `model_request()` with `model` param |
| Language detection | `client.messages.create()` with `client` param | `model_request()` with `model` param |
| Config model strings | `"claude-sonnet-4-5-20250929"` | `"anthropic:claude-sonnet-4-5-20250929"` |
| Direct `anthropic` dep | `anthropic>=0.40.0` in pyproject.toml | Transitive via `pydantic-ai-slim[anthropic]` |

---

## 7. Multi-Currency: Currency-Agnostic Fields + Static FX Rates

**Decision**: Rename all CFA-specific fields (`balance_cfa`, `amount_cfa`, `fee_cfa`) to currency-agnostic names (`balance`, `amount`, `fee`) with a separate `currency` field, and use static exchange rates rather than a live FX API.

**Context**: The original data layer assumed all values were in CFA Francs (XOF). Expanding to 10 currencies required a field rename across the entire codebase (models, accounts, transactions, fees, tools, prompts, tests) plus FX conversion logic.

**Reasoning**:

- **Static rates are sufficient for a demo**: Live FX APIs add infrastructure (API keys, rate limiting, caching, staleness handling) for no additional signal. Static rates in a `DEMO_EXCHANGE_RATES` dict are deterministic, testable, and always available.
- **USD normalization for fee tiers**: Fee tiers are defined in USD-equivalent amounts. All currencies are converted to USD for tier matching, then fees are expressed in the source currency. This avoids maintaining separate tier definitions per currency.
- **Currency-aware formatting**: A `format_currency()` helper handles symbol position, decimal places, and thousands separators per currency (e.g., `£1,200.00` vs `150,000 NGN` vs `45,000 KES`).

**Trade-off accepted**: The field rename touched 12+ files in a single refactor commit. This was done as a standalone pre-phase commit before adding new data, keeping the diff reviewable.

---

## 8. RAG: ChromaDB In-Memory vs. Hosted Vector DB

**Decision**: Use ChromaDB in-memory for policy document retrieval with OpenAI `text-embedding-3-small` for embeddings, with a fallback chain to keyword search.

**Context**: The `get_policy()` tool originally did exact topic matching against a dict. RAG replaces this with semantic search over embedded policy documents.

**Reasoning**:

- **Zero infrastructure**: ChromaDB in-memory requires no external service. Embeddings are generated at startup from the policy documents and stored in a module-level collection. No persistence needed — the corpus is small (~15 documents) and rebuilds in seconds.
- **OpenAI `text-embedding-3-small`**: Better multilingual support than alternatives (handles French and Swahili policy queries), and the OpenAI API key is already required for voice features.
- **Fallback chain**: If the embedding API fails or ChromaDB errors, the tool falls back to the original keyword-based `get_policy()` / `search_policies()`. The user always gets an answer.
- **Relevance scoring**: Vector search returns ranked results with similarity scores, letting the agent cite the most relevant policy rather than requiring an exact topic match.

**Trade-off accepted**: Embeddings are rebuilt on every server restart. For ~15 documents this takes <2 seconds. A persistent vector store (Pinecone, Weaviate) would be needed at scale.

---

## 9. Multi-Agent Routing: Haiku Classifier + Tool Subsets

**Decision**: Use a lightweight Haiku-based intent classifier to route queries to specialist agents (support, fraud, escalation), each with a subset of the available tools.

**Context**: The original system had a single support agent with all 8 tools. Multi-agent routing adds an orchestrator that classifies intent before dispatching to a specialist.

**Reasoning**:

- **Haiku for classification speed**: Intent classification doesn't need Sonnet's reasoning depth. Haiku classifies in ~200-400ms, keeping the added latency before first token minimal.
- **Structured output**: The classifier returns a pydantic model (`AgentType` enum), not free text. This eliminates parsing ambiguity.
- **Tool subsetting**: Each specialist gets only the tools relevant to its domain. The fraud agent gets `lookup_transaction`, `get_transactions`, `get_policy`, and `create_support_ticket` — it can investigate and escalate but can't check balances or calculate fees. This constrains each agent's behavior without relying solely on system prompts.
- **Slot into existing pipeline**: The orchestrator replaces the single `agent.run()` call in `core.py`. Guardrails, language detection, and streaming all stay in one place — no duplication.
- **Default fallback**: Any classification failure (timeout, malformed output, unknown intent) routes to the support agent. The system never fails to respond.

**Trade-off accepted**: Adds one LLM call (~300ms) before the specialist agent runs. For a demo this is acceptable. At scale, a local classifier (fasttext) could replace Haiku for near-zero latency.

---

## 10. PostgreSQL Persistence: Feature-Flagged with In-Memory Fallback

**Decision**: Add optional PostgreSQL session persistence via asyncpg, controlled by `USE_POSTGRES` and `DATABASE_URL` environment variables, with the in-memory store as the default.

**Context**: The in-memory session store works well for demos but doesn't persist across server restarts. PostgreSQL adds production-grade persistence while keeping the zero-infrastructure default.

**Reasoning**:

- **asyncpg over SQLAlchemy/ORM**: asyncpg is a pure async PostgreSQL driver with excellent performance. Raw SQL with parameterized queries keeps the abstraction minimal and the queries visible. No ORM overhead for a single-table schema.
- **Same interface**: `PostgresSessionStore` implements the exact same methods as the in-memory `SessionStore`. The server selects which store to use based on the feature flag at startup. No other code needs to change.
- **Atomic operations**: `get_messages()` uses `UPDATE...SET last_accessed = now() WHERE id = $1 AND last_accessed > now() - interval RETURNING messages` — a single atomic query that touches the session, checks expiry, and returns messages. This prevents TOCTOU races that the original separate-SELECT-then-UPDATE pattern would have.
- **Auto-migration**: Raw SQL migration files in `src/db/migrations/` are applied on pool initialization. `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` make migrations idempotent.
- **Feature-flagged**: `USE_POSTGRES=false` (default) means the project runs with zero database setup, preserving the quick-start experience. Setting it to `true` enables persistence for production deployments.

**Trade-off accepted**: No migration tool (Alembic). For a single-table schema with idempotent DDL, raw SQL files are simpler. A migration framework would be needed if the schema grew.

---

## 11. CI Eval Pipeline: 20 Critical Cases per PR

**Decision**: Run a curated subset of 20 critical eval cases on every PR via GitHub Actions, with threshold gates for groundedness (≥85%), hallucination-free (≥90%), and compliance (100%).

**Context**: The full eval suite (155+ cases) is too expensive and slow for CI (~$2-4, several minutes). A critical subset provides fast, cheap quality gates.

**Reasoning**:

- **Curated, not random**: The 20 cases are hand-picked to cover the highest-risk scenarios: balance accuracy, fee calculations, ID masking, injection defense, cross-currency queries. They're defined in `ci_subset.py` as a list of case IDs.
- **Threshold gates**: Groundedness ≥85% catches regressions where the agent fabricates data. Hallucination-free ≥90% catches new hallucination patterns. Compliance = 100% is non-negotiable (ID masking must never break).
- **PR comment**: The workflow posts eval results as a PR comment, making failures visible without digging into logs.
- **Monkey-patching for case filtering**: The CI runner temporarily replaces `harness_mod.get_test_cases` to return only the critical subset, then restores the original. This reuses the existing harness without adding a filtering parameter to its API.

**Trade-off accepted**: 20 cases is a small sample. Edge cases in the remaining 135+ cases could regress without detection. The full suite should run nightly or on release branches.
