# Understanding a codebase before editing

The goal is to form a correct mental model before changing anything.

## Steps

1. **Locate, do not assume.** Use search to find definitions and call sites
   before reading. Prefer symbol-aware search over raw text search when the
   repository supports it.
2. **Read the smallest slice that matters.** Read the entry point, the specific
   function, and its callers/callees. Avoid dumping whole files.
3. **Trace one flow end to end.** Follow a single request or test through the
   code to understand how data moves.
4. **Find the tests.** Tests are executable documentation of expected behavior;
   read the ones that cover the area you will touch.

## When to ask instead of guessing

- The user's goal is ambiguous (what should this do, what are the inputs/outputs).
- Multiple reasonable designs exist and the choice changes the implementation.
- The change affects a public API, a security boundary, or persisted data.

Asking one precise question is cheaper than implementing the wrong thing.
