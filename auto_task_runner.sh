#!/usr/bin/env bash
# Simplified automated task runner for spec-workflow MCP
set -euo pipefail

# Configuration
SPEC_NAME="${SPEC_NAME:-test-optimization}"
PROJECT_PATH="${PROJECT_PATH:-$(pwd)}"
TASK_LIMIT="${TASK_LIMIT:-3}"

echo "🚀 Auto Task Runner for Spec: $SPEC_NAME"
echo "📁 Project: $PROJECT_PATH"
echo "🎯 Task Limit: $TASK_LIMIT"
echo ""

for ((i=1; i<=TASK_LIMIT; i++)); do
    echo "--- Task Iteration $i/$TASK_LIMIT ---"
    
    # Simple, direct command - let Claude handle the MCP workflow naturally
    claude -p "Work on the next pending task for spec '$SPEC_NAME'" --max-turns 10 --dangerously-skip-permissions
    
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "❌ Task iteration $i failed with exit code $exit_code"
        break
    fi
    
    echo "✅ Task iteration $i completed"
    echo ""
done

echo "🏁 Auto task runner finished"