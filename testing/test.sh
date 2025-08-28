#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$(dirname "$0")"   # into testing/

COV=0
while [[ ${1:-} == --* ]]; do
  case "$1" in
    --cov)
      COV=1
      ;;
    *)
      break
      ;;
  esac
  shift
done

echo "🧪 Activity Heatmap Mobile App Tests"
echo "Coverage:     $([[ $COV -eq 1 ]] && echo 'ON' || echo 'OFF')"
echo

# Activate virtual environment if it exists
if [ -f "test_venv/bin/activate" ]; then
    echo "🐍 Activating Python virtual environment..."
    source test_venv/bin/activate
fi

if [[ $COV -eq 1 ]]; then
  echo "📦 Instrumenting JS in server/..."
  (cd "$REPO_ROOT" && npm run --silent cov:js:instrument)
  export INSTRUMENT_JS=1
fi

# Run your Python test runner; append flags if coverage
PY_ARGS=("$@") # Pass through any other arguments
[[ $COV -eq 1 ]] && PY_ARGS+=("--cov")

# Check which runner to use
RUNNER="run_tests.py"
if [[ " ${PY_ARGS[*]} " =~ " --direct " ]]; then
    RUNNER="run_tests_direct.py"
fi

echo "🚀 Running tests with enhanced runner ($RUNNER)..."
python3 $RUNNER "${PY_ARGS[@]}"

if [[ $COV -eq 1 ]]; then
  echo "🧮 Rendering JS coverage report..."
  # Use npx from the repo root to ensure it finds the dependencies
  (cd "$REPO_ROOT" && npx nyc report \
    --temp-dir "$REPO_ROOT/testing/reports/coverage/js" \
    --reporter=html --report-dir "$REPO_ROOT/testing/reports/coverage/js/html" \
    --reporter=lcov \
    --reporter=cobertura || true)

  echo
  echo "✅ Python HTML: file://$(cd "$REPO_ROOT" && pwd)/testing/reports/coverage/python/html/index.html"
  echo "✅ JS HTML:     file://$(cd "$REPO_ROOT" && pwd)/testing/reports/coverage/js/html/index.html"
  echo "✅ CSS HTML:    file://$(cd "$REPO_ROOT" && pwd)/testing/reports/coverage/css/html/index.html"
  echo "✅ DOM HTML:    file://$(cd "$REPO_ROOT" && pwd)/testing/reports/coverage/dom/html/index.html"
fi

echo "🎉 Testing complete!"
