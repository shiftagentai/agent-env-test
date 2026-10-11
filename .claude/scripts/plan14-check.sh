#!/bin/bash
# Plan 14 dev e2e fixture for script.run routines: reads the event context on stdin, logs to
# stderr, and prints one JSON result. `wake` echoes trigger.body.wake so the e2e can exercise
# both branches of wake_agent.when.
ctx=$(cat)
echo "plan14-check: ${#ctx} bytes of context, run=${SHIFTAGENT_RUN_ID:-?} routine=${SHIFTAGENT_ROUTINE:-?}" >&2
wake=$(printf '%s' "$ctx" | sed -n 's/.*"wake":\s*\(true\|false\).*/\1/p' | head -1)
printf '{"wake": %s, "note": "from the tenant tree", "ctx_bytes": %d, "run": "%s"}\n' "${wake:-false}" "${#ctx}" "${SHIFTAGENT_RUN_ID:-}"
