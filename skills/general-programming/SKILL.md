---
name: general-programming
description: "Use for general software engineering on a repository: implementing features, fixing bugs, refactoring, writing and running tests, and reviewing code. Trigger when the user asks to build, change, debug, test, or explain code."
license: MIT
---

# General Programming

You are executing the general-programming skill. It governs how to approach any
software engineering task on the current repository, regardless of language or
domain. This skill is model-agnostic: it never selects a model. The harness's
dynamic router chooses local vs cloud per turn from the task text, tool names
and instructions.

## Core principles

1. **Understand before editing.** Locate and read the relevant code first. Do
   not guess file paths, symbol names or behavior.
2. **Make the smallest change that works.** Prefer surgical edits over rewrites.
   Do not fix unrelated issues you notice along the way unless asked.
3. **Verify, do not assert.** Run the smallest build/test/lint command that
   covers the change and read the output before declaring success.
4. **Preserve existing behavior.** A change is complete only when existing
   behavior is preserved and the new behavior is verified.

## Workflow

Execute these stages in order. Do not skip a stage.

### 1 — Understand

- Locate the relevant files and symbols (search, then read).
- Identify the entry points, the data flow, and the tests that cover the area.
- If the intent is ambiguous, ask a clarifying question instead of inventing
  requirements. See `references/understanding.md`.

### 2 — Plan

- State the concrete change: which files, which functions, which tests.
- Choose the smallest set of edits that satisfies the request.
- Flag anything that will touch shared code, public APIs, or persisted state.

### 3 — Implement

- Apply precise, complete, surgical changes.
- Follow the repository's existing style and conventions.
- Comment only where a line genuinely needs clarification; do not comment
  otherwise.

### 4 — Test

- Run the smallest command covering the change (targeted first), and escalate
  to the full suite only when targeted results require it.
- If the change is not covered by tests, add the minimal test that exercises it.
- See `references/testing.md`.

### 5 — Verify

- Confirm the change compiles/type-checks and the tests pass.
- Review the diff for accidental or unrelated edits.
- See `references/verification.md`.

## Routing behavior

This skill has no model-selection logic. The harness router classifies turns
with the generic `code` and `reasoning` task classes, so heavy programming
turns (implement, refactor, debug, patch) route to the cloud pool while simple
turns (explain, summarize) route to the local pool. To change that, edit
`config/model_router.yaml` — not this skill.

## Language-agnostic checklist

Before finishing, confirm:

- [ ] The change addresses the request, not a reinterpretation of it.
- [ ] Existing tests still pass (or a documented, justified reason to update them).
- [ ] New behavior has a test or a reproducible verification step.
- [ ] No secrets, debug prints, or temporary files are left behind.
- [ ] The diff contains no unrelated changes.
