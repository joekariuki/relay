# Design Decisions

This document captures key architectural and technical decisions made during the development of Relay, along with the reasoning behind each choice.

---

## 1. Direct SDK Usage vs. LLM Frameworks (LangChain / LangGraph)

**Decision**: Use the Anthropic Python SDK and OpenAI Python SDK directly instead of frameworks like LangChain or LangGraph.

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

**Where each SDK is used**:

| SDK | Module | Purpose |
|-----|--------|---------|
| `anthropic.AsyncAnthropic` | `src/agent/core.py` | Main agent loop (Claude Sonnet, tool-use) |
| `anthropic.AsyncAnthropic` | `src/agent/router.py` | Language detection (Claude Haiku) |
| `anthropic.AsyncAnthropic` | `src/eval/groundedness.py` | LLM-as-judge groundedness scoring |
| `anthropic.AsyncAnthropic` | `src/eval/hallucination.py` | LLM-as-judge hallucination detection |
| `anthropic.AsyncAnthropic` | `src/eval/language_quality.py` | LLM-as-judge language quality |
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
