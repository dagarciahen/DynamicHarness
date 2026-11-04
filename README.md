<h1 align="center">DynamicHarness</h1>

<p align="center">
  <strong>Reason and act over a repository with dynamic local/cloud model routing.</strong>
</p>

<p align="center">
  A hand-written, LangChain-free agent harness. Tools, permissions, persistent
  state, and model selection all live outside the model — including a router
  that chooses, per turn, between a local model (Ollama) and a cloud API
  (any OpenAI-compatible endpoint).
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img alt="python >=3.12" src="https://img.shields.io/badge/python-%3E%3D3.12-3776AB?logo=python&logoColor=white"></a>
  <img alt="version 1.0.1" src="https://img.shields.io/badge/version-1.0.1-007EC6">
</p>

DynamicHarness is a general agent harness adapted from
[AgentLoom](https://github.com/linora-u/AgentLoom). On top of the base agent loop it adds one differentiating layer a **dynamic model router** and ships `paper2code` and `general-programming` as **Skills**.

## Why DynamicHarness

### One harness, local or cloud

The same agent runs against a local model, a cloud API, or both. A
`RoutingPolicy` declares local and cloud **pools** (sets of `model_type` values)
and **task classes**. For every model turn the router picks a pool and model by matching the turn against three signals:

1. **Task type:**  simple turns (summarize, extract, greet) prefer local;
   `research`/`code`/`reasoning` turns prefer cloud.
2. **Resource load:** the local pool is skipped when Ollama is unreachable or
   above `local_max_load` (an injectable health probe).
3. **Budget:** a token counter fed by provider-reported usage; when
   `cloud_token_budget` is spent, `over_budget_behavior` decides (default: fall
   back to local).

Every decision is recorded with its pool, model, task class, reason, and confidence evidence, not a guess.

### Skills load on demand

Skills are Markdown instruction packages (`SKILL.md`) plus optional scripts that the harness discovers by frontmatter metadata and loads only when a task matches their description. The harness has no skill-specific logic.

- **`paper2code:`** converts an arxiv paper into a minimal, citation-anchored
  Python implementation (adapted from [paper2code](https://github.com/PrathamLearnsToCode/paper2code)).
- **`general-programming:`**  everyday software engineering: implement, fix,
  refactor, test, and review code.

### Hand-written, permissions outside the model

File read/write, shell execution, tests, and permissions are governed outside the model.

## Quick start

```bash
git clone https://github.com/dagarciahen/DynamicHarness
cd DynamicHarness
uv sync --group dev
```

Create the model configuration:

```bash
cp config/model.example.yaml config/model.yaml
```

`config/model.yaml` is ignored by Git and provides the project's model catalog.
Select models in Agent YAML with `model_type`.

## Model routing

Routing is **opt-in**. Enable it:

```bash
cp config/model_router.example.yaml config/model_router.yaml
# set routing.enabled: true
```

Declare every pooled `model_type` in `config/model.yaml`:

```yaml
model:
  default_model_type: powerful
  ollama:            # local pool
    adapter: openai_chat
    model: "ollama/qwen2.5-coder:14b"
    base_url: "http://localhost:11434"
    api_key: "ollama"
  powerful:          # cloud pool (DeepSeek)
    adapter: openai_chat
    model: "openai/<fast-model-id>"
    api_key: "<api-key>"
    base_url: "https://<openai-compatible-endpoint>"
    tool_choice: "auto"
```

`AGENTLOOM_MODEL_ROUTER_CONFIG=/path/to/policy.yaml` overrides the policy file location for a single invocation. See [`docs/en/model_routing.md`](docs/en/model_routing.md) for the full contract.

## Layout

```text
src/
  execution/model_router/   # the dynamic routing layer
  execution/skills/         # SKILL.md discovery + on-demand activation
  app/                      # agent factory + routing integration seam
skills/
  paper2code/               # arxiv paper -> code Skill
  general-programming/      # general software-engineering Skill
tests/
  model_router_test/        # router + skill integration tests
config/
  model_router.example.yaml # opt-in routing policy
  model.example.yaml        # model profiles incl. a local `ollama` example
```

## Test

```bash
uv sync --group dev
# Linux/macOS
.venv/bin/python -m pytest tests/model_router_test -v
# Windows --> TODO
.venv\Scripts\python.exe -m pytest tests\model_router_test -v
```

The router core (`policy`, `budget`, `health`, `router`) is stdlib-only and
unit-testable without the full dependency tree.
