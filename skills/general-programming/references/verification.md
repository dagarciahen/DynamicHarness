# Verifying a change is complete

## Definition of done

A change is complete when all of the following hold:

1. **Behavior** — the change does what was requested and preserves existing
   behavior elsewhere.
2. **Tests** — the relevant tests pass, and new behavior is covered or has a
   reproducible manual verification step.
3. **Diff** — the diff contains only the intended edits and no secrets, debug
   prints, or temporary artifacts.
4. **Build** — the code compiles, type-checks, or lints cleanly where the
   repository has such gates.

## Final review checklist

- [ ] Re-read the diff top to bottom.
- [ ] Confirm no unrelated "drive-by" changes slipped in.
- [ ] Confirm generated files, caches, and scratch files are not committed.
- [ ] Record how the change was verified (command + result), not just that it
      "should work".
