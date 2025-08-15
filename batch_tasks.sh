#!/usr/bin/env bash
# Batch task runner for pimzino-spec-workflow-mcp via Claude Code CLI
set -Eeuo pipefail

# --- Config ---
MCP_SERVER_ALIAS="spec-workflow"
SPEC_NAME="${SPEC_NAME:-test-optimization}"
PROJECT_PATH="${PROJECT_PATH:-$(pwd)}"
TASK_LIMIT="${TASK_LIMIT:-3}"
CLAUDE_FLAGS=(--output-format stream-json --max-turns 6 --dangerously-skip-permissions --verbose)

# Optional: start dashboard automatically (0 = no, 1 = yes)
START_DASHBOARD="${START_DASHBOARD:-0}"
SPECDASH_PORT="${SPECDASH_PORT:-3010}"
LOG_DIR="${LOG_DIR:-logs}"
mkdir -p "$LOG_DIR"

require() { command -v "$1" >/dev/null 2>&1 || { echo "Error: '$1' not found" >&2; exit 1; }; }
require claude
require jq

log() { printf '%s\n' "$*" >&2; }

# Extract the final tool_result text blob from Claude's stream-json
extract_tool_json() {
  jq -rc '
    .message?.content[]? |
    select(.type=="tool_result") |
    .content[]? |
    select(.type=="text") |
    .text
  ' | tail -n 1
}

call_tool() {
  local tool="$1" params="$2"
  local prompt
  prompt=$(cat <<EOF
Call the MCP tool "${tool}" with exactly these JSON args:
${params}
Return ONLY the raw tool JSON result, with no extra text or explanation.
EOF
)
  claude -p "$prompt" "${CLAUDE_FLAGS[@]}" | tee -a "${LOG_DIR}/tool_${tool//[^A-Za-z0-9_]/_}.jsonl" | extract_tool_json
}

ensure_dashboard_started=0
ensure_dashboard() {
  [[ "$START_DASHBOARD" != "1" ]] && return 0
  # If something is already listening on the port, do nothing
  if (command -v ss >/dev/null && ss -lnt | grep -q ":${SPECDASH_PORT} ") || \
     (command -v netstat >/dev/null && netstat -lnt | grep -q ":${SPECDASH_PORT} "); then
    log "[runner] Dashboard already running on :${SPECDASH_PORT}"
    return 0
  fi
  log "[runner] Starting MCP dashboard on :${SPECDASH_PORT} ..."
  nohup npx -y @pimzino/spec-workflow-mcp@latest "$PROJECT_PATH" --dashboard --port "$SPECDASH_PORT" \
    >"${LOG_DIR}/specdash.log" 2>&1 & DASH_PID=$!
  ensure_dashboard_started=1
  # best-effort wait
  sleep 2
}

cleanup() {
  if [[ "$START_DASHBOARD" == "1" && "$ensure_dashboard_started" == "1" && -n "${DASH_PID:-}" ]]; then
    log "[runner] Stopping dashboard (pid ${DASH_PID})"
    kill "${DASH_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

TOOL_MANAGE="mcp__${MCP_SERVER_ALIAS}__manage-tasks"
TOOL_SPECLIST="mcp__${MCP_SERVER_ALIAS}__spec-list"

# (Optional) Start dashboard
ensure_dashboard

# 0) Verify spec exists (use any() to avoid last-element trap)
log "🔎 Checking that spec '${SPEC_NAME}' exists in ${PROJECT_PATH} ..."
SPECS_JSON=$(call_tool "$TOOL_SPECLIST" "$(jq -nc --arg p "$PROJECT_PATH" '{projectPath:$p}')")
echo "$SPECS_JSON" | jq -e --arg n "$SPEC_NAME" '.data.specs | any(.name == $n)' >/dev/null \
  || { log "Error: Spec '$SPEC_NAME' not found. Available: $(echo "$SPECS_JSON" | jq -r '.data.specs[].name' | xargs)"; exit 2; }

log "🚀 Starting batch task execution for spec: $SPEC_NAME (limit: $TASK_LIMIT)"
for (( i=1; i<=TASK_LIMIT; i++ )); do
  log "🔎 Getting next pending task ($i/$TASK_LIMIT)..."
  # Optional: refresh tasks here if your server benefits from a sync step
  # REFRESH_JSON=$(call_tool "$TOOL_MANAGE" "$(jq -nc --arg p "$PROJECT_PATH" --arg s "$SPEC_NAME" '{projectPath:$p, specName:$s, action:"refresh-tasks"}')")

  NEXT_JSON=$(call_tool "$TOOL_MANAGE" "$(jq -nc --arg p "$PROJECT_PATH" --arg s "$SPEC_NAME" '{projectPath:$p, specName:$s, action:"next-pending"}')")
  NEXT_ID=$(jq -r '.data.nextTask?.id // empty' <<<"$NEXT_JSON")

  if [[ -z "$NEXT_ID" ]]; then
    INPROG_COUNT=$(jq -r '(.data.inProgressTasks // []) | length' <<<"$NEXT_JSON")
    if [[ "$INPROG_COUNT" -gt 0 ]]; then
      log "⏳ No pending tasks. Tasks in progress: $(jq -r '(.data.inProgressTasks // [])[].id' <<<"$NEXT_JSON" | xargs)"
    else
      log "🎉 All tasks for spec '$SPEC_NAME' are completed!"
    fi
    break
  fi

  log "⏩ Marking task ${NEXT_ID} as in-progress..."
  SET_JSON=$(call_tool "$TOOL_MANAGE" "$(jq -nc --arg p "$PROJECT_PATH" --arg s "$SPEC_NAME" --arg id "$NEXT_ID" '{projectPath:$p,specName:$s,action:"set-status",taskId:$id,status:"in-progress"}')")
  jq -e 'select(.success==true)' <<<"$SET_JSON" >/dev/null || { log "Error: Failed to set in-progress. Response: $SET_JSON"; exit 3; }

  log "🛠  Implementing task ${NEXT_ID} ..."
  impl_prompt=$(cat <<'PROMPT'
Follow the MCP workflow rules. Implement the current task now.
- You can read required spec documents using the spec-workflow tools.
- Edit files, run commands, and run tests as needed. Assume permissions are granted.
- When finished, output ONLY the JSON: {"ok":true,"notes":"<1-2 line summary>"}
PROMPT
)
  IMPL_JSON=$(
    claude -p "Implement task ${NEXT_ID} in spec ${SPEC_NAME} at ${PROJECT_PATH}. ${impl_prompt}" "${CLAUDE_FLAGS[@]}" \
    | tee -a "${LOG_DIR}/task_${NEXT_ID}.jsonl" \
    | jq -rc 'select(.type=="assistant") | .message?.content[]? | select(.type=="text") | .text' \
    | tail -n 1
  )

  if ! jq -e 'try (fromjson|.ok==true) catch false' <<<"$IMPL_JSON" >/dev/null; then
    log "❌ Implementation step for task ${NEXT_ID} did not return ok:true JSON. Output follows:"
    printf '%s\n' "$IMPL_JSON"
    exit 4
  fi

  log "✅ Marking task ${NEXT_ID} as completed..."
  DONE_JSON=$(call_tool "$TOOL_MANAGE" "$(jq -nc --arg p "$PROJECT_PATH" --arg s "$SPEC_NAME" --arg id "$NEXT_ID" '{projectPath:$p,specName:$s,action:"set-status",taskId:$id,status:"completed"}')")
  jq -e 'select(.success==true)' <<<"$DONE_JSON" >/dev/null || { log "Error: Failed to set completed. Response: $DONE_JSON"; exit 5; }

  log "✔️  Task ${NEXT_ID} completed."
  log "-------------------------------------------------"
done

log "👋 Batch run finished. Re-run to process the next batch."
