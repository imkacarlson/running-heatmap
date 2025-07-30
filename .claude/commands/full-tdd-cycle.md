# /project:full-tdd-cycle

## Purpose
Execute a full TDD workflow for the Claude-backed hybrid Android app. Use the feature I describe as `$ARGUMENTS`.

## Instructions
You will guide me through the following steps based on the feature name or description that I provide in place of `$ARGUMENTS`:

1. Write a failing Appium UI test in Python to validate the feature (using my existing test harness and conventions).
2. Ask me to run the test and confirm it fails.
3. After confirmation, implement the feature in both mobile (Capacitor) and web versions.
4. Ask me to run the test again and confirm it passes.
5. Propose and write additional tests (edge cases, error conditions, performance).
6. Make suggestions for UX, memory, or performance improvements if relevant.
7. Update any documentation or inline comments related to the feature.
8. Confirm completion and check if I'm satisfied.

When I say "reset", start over from step 1. Use `$ARGUMENTS` exactly once at the beginning so the feature name is clear in the prompt.

**Feature to implement:** `$ARGUMENTS`
