# Testing a change

## Choose the smallest command that covers the change

1. Run the specific test file or test name for the code you touched.
2. Run the package or subsystem suite if the change is cross-cutting.
3. Run the full suite only when targeted results require it or the change is
   foundational.

## Interpret output honestly

- Read the failure output before concluding anything.
- A pass means the assertions passed; it does not prove the change is correct
  in every environment.
- A skipped or not-collected test is not a pass.

## Add coverage when it is missing

- If the change has no test, add the minimal test that exercises it.
- Prefer deterministic assertions over timing- or network-dependent ones.
- Do not write tests that only assert the implementation is a tautology.
