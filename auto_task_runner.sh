#!/usr/bin/env bash
# Auto Task Runner with real-time streaming + logging
set -Eeuo pipefail

# Cleanup function for interrupted runs
cleanup() { 
    echo "" 
    echo "🛑 Runner interrupted" 
}
trap cleanup INT TERM

# --- Config ---
SPEC_NAME="${SPEC_NAME:-test-optimization}"
PROJECT_PATH="${PROJECT_PATH:-$(pwd)}"
TASK_LIMIT="${TASK_LIMIT:-1}"
LOG_DIR="${LOG_DIR:-./logs}"

mkdir -p "$LOG_DIR"

echo "🚀 Auto Task Runner for Spec: $SPEC_NAME"
echo "📁 Project: $PROJECT_PATH"
echo "🎯 Task Limit: $TASK_LIMIT"
echo ""

# Simple dependency check
command -v claude >/dev/null 2>&1 || { echo "claude CLI not found in PATH"; exit 127; }

for ((i=1; i<=TASK_LIMIT; i++)); do
  ts="$(date +'%Y%m%d_%H%M%S')"
  LOG_FILE="${LOG_DIR}/${SPEC_NAME}_${ts}_iter${i}.log"
  echo "--- Task Iteration $i/$TASK_LIMIT ---"
  echo "📝 Logging to: $LOG_FILE"
  echo "⏱  Started: $(date +'%F %T')"
  echo ""

  # Stream JSON output and parse for human-readable display
  MAX_TURNS=30
  current_turn=0
  first_assistant_msg=true
  
  stdbuf -i0 -o0 -e0 claude -p "Work on the next un completed task for spec ${SPEC_NAME}" \
    --output-format stream-json --max-turns $MAX_TURNS --dangerously-skip-permissions --verbose 2>&1 | \
  while IFS= read -r line; do
    # Save raw JSON to log
    echo "$line" >> "$LOG_FILE"
    
    # Parse and display human-readable content
    if command -v jq >/dev/null 2>&1; then
      # Extract message type
      msg_type=$(echo "$line" | jq -r '.type // empty' 2>/dev/null)
      
      case "$msg_type" in
        "system")
          subtype=$(echo "$line" | jq -r '.subtype // empty' 2>/dev/null)
          if [[ "$subtype" == "init" ]]; then
            session_id=$(echo "$line" | jq -r '.session_id // empty' 2>/dev/null)
            echo "🔄 Starting session: ${session_id:0:8}..."
            echo ""
          fi
          ;;
        "assistant")
          # Check if this is a new assistant message (start of new turn) - only count messages with IDs
          message_id=$(echo "$line" | jq -r '.message.id // empty' 2>/dev/null)
          if [[ -n "$message_id" ]]; then
            if [[ "$first_assistant_msg" == "false" ]]; then
              echo -e "\n"  # Add blank line between turns
            fi
            current_turn=$((current_turn + 1))
            echo "💬 Turn $current_turn/$MAX_TURNS:"
            first_assistant_msg=false
          fi
          
          # Extract and display assistant text content
          text=$(echo "$line" | jq -r '.message.content[]? | select(.type == "text") | .text // empty' 2>/dev/null)
          if [[ -n "$text" ]]; then
            echo -n "$text"
          fi
          
          # Show tool usage
          tool_name=$(echo "$line" | jq -r '.message.content[]? | select(.type == "tool_use") | .name // empty' 2>/dev/null)
          if [[ -n "$tool_name" ]]; then
            echo -e "\n🔧 Using tool: $tool_name"
          fi
          ;;
        "result")
          echo ""  # Final newline before result
          subtype=$(echo "$line" | jq -r '.subtype // empty' 2>/dev/null)
          if [[ "$subtype" == "success" ]]; then
            cost=$(echo "$line" | jq -r '.total_cost_usd // empty' 2>/dev/null)
            duration=$(echo "$line" | jq -r '.duration_ms // empty' 2>/dev/null)
            turns=$(echo "$line" | jq -r '.num_turns // empty' 2>/dev/null)
            echo "✅ Completed in ${current_turn}/${MAX_TURNS} turns (${duration}ms, \$${cost})"
          else
            echo "❌ Task failed: $subtype"
          fi
          ;;
      esac
    else
      # Fallback without jq - just show raw JSON
      echo "$line"
    fi
  done
  exit_code=${PIPESTATUS[0]}

  if [ $exit_code -ne 0 ]; then
    echo ""
    echo "❌ Task iteration $i failed with exit code $exit_code"
    echo "📄 See log: $LOG_FILE"
    break
  fi

  echo ""
  echo "✅ Task iteration $i completed"
  echo "📄 Log saved: $LOG_FILE"
  echo ""
done

echo "🏁 Auto task runner finished"