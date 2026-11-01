# Dynamic model routing

DynamicHarness resolves one `model_type` per Agent from `config/model.yaml`. The
model router adds an opt-in layer on top of that: for every model turn it
decides whether a **local** (Ollama) or a **cloud** (OpenAI-compatible, e.g.
DeepSeek) model should run, based on task type, resource load and budget.

The harness itself stays paper-agnostic and runtime-neutral. Routing is a
generic capability; a Skill such as `paper2code` can later hint a preferred
pool without the harness containing any paper-specific logic.

## How it works

```
config/model_router.yaml   ->   RoutingPolicy   ->   ModelRouter
                                                        |
                                             classifies each turn
                                                        v
              local pool (Ollama)  <---->  cloud pool (DeepSeek/...)
```

The decision is made per model turn inside a `RoutingTurnAdapter`, which wraps
the candidate `ModelTurnBinding` objects and is itself wrapped in a canonical
`ModelTurnBinding` (`model_type: "routing"`). Existing runtimes accept it
unchanged because it satisfies the same contract.

A turn is classified by matching its text, tool names and instructions against
the `task_classes` patterns. The winning class declares a `prefer`red pool.
Local pools are skipped when the backend is unreachable or above
`local_max_load`; cloud pools are skipped once the token budget is exhausted
(`over_budget_behavior: local`) unless the policy allows overage. If nothing
matches, `final_resort` picks a relaxed fallback or raises.

## Enabling routing

1. Copy the example policy:

   ```bash
   cp config/model_router.example.yaml config/model_router.yaml
   ```

2. Set `routing.enabled: true` in that file.

3. Declare every pooled `model_type` in `config/model.yaml`. For Ollama, add a
   profile whose `model` uses the LiteLLM `ollama/` prefix and a local
   `base_url` (see `config/model.example.yaml`). For DeepSeek, use an
   OpenAI-compatible profile pointing at `https://api.deepseek.com`.

With the policy file absent or `enabled: false`, `Agent._resolve_model_binding`
behaves exactly as before, so routing never changes the default path.

`DynamicHarness_MODEL_ROUTER_CONFIG=/path/to/policy.yaml` overrides the policy file
location for a single invocation.

## Local-only and cloud-only modes

The same harness works with either backend:

- **Local only**: declare only a local pool and set `default_pool` to it. No
  cloud credentials are required.
- **Cloud only**: declare only a cloud pool. The health probe is never needed.
- **Both**: the default setup above, with the router deciding per turn.

## Budget and load signals

- **Budget** is a token counter (`BudgetMeter`) fed by the provider-reported
  token usage after each cloud turn. The limit and over-budget behavior come
  from `routing.budget`.
- **Load** is an injectable `LocalHealthProbe`. `OllamaHealthProbe` reports
  Ollama reachability via `GET http://localhost:11434/api/tags`. Plug in a
  different probe to model GPU/CPU load.

## Skills and routing

Skills are model-context packages loaded on demand; they never hard-code a
model choice and the harness contains no skill-specific logic. Classification
is driven by the turn's text, tool names and instructions, so a heavy Skill such
as the shipped `paper2code` (see [`skills_config`](skills_config.md)) naturally
routes to the cloud pool through the generic `code`/`reasoning` task classes,
while a summary request goes local — with no paper-specific rule anywhere in the
framework.

## Decision evidence

`RoutingTurnAdapter.history` records each `RoutingDecision`
(`pool`, `model_type`, `task_class`, `reason`, `confidence`). This mirrors the
harness principle that runs produce evidence rather than terminal guesses.

## Constraints (v1)

- All pooled model profiles must share one wire adapter kind. Ollama and
  DeepSeek are both OpenAI-compatible, so `openai_chat` is the expected value.
- Per-turn temperature/max-token overrides are not yet propagated through the
  router; only `stop` and `tool_choice` are forwarded.
