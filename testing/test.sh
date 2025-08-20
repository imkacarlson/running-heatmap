#!/bin/bash
set -euo pipefail

PERF=0
ARGS=()

# Parse args (capture everything except --perf)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --perf) PERF=1; shift ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
set -- "${ARGS[@]}"

echo "🧪 Activity Heatmap Mobile App Tests"
echo "============================================"

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source test_venv/bin/activate

# Timestamped output directory
STAMP=$(date +%Y%m%d-%H%M%S)
OUTDIR="testing/reports/perf/pyi-$STAMP"
OUTHTML="$OUTDIR/profile.html"

mkdir -p "$OUTDIR"

# Wrap pytest invocation so we only touch one place
run_pytest() {
  # Run the enhanced test suite
  echo "🚀 Running tests with enhanced runner..."
  python run_tests.py "$@"
}

if [[ "$PERF" -eq 0 ]]; then
  run_pytest "$@"
  echo "🎉 Testing complete!"
else
  # Check dependency early for a clearer error
  if ! python -c "import pyinstrument" >/dev/null 2>&1; then
    echo "pyinstrument not installed in this venv. Install via: pip install -r testing/requirements.txt" >&2
    exit 2
  fi

  # One HTML flamegraph for the entire run
  echo "🔥 Running tests with performance profiling..."
  python -m pyinstrument -r html -o "$OUTHTML" -m run_tests "$@"

  echo "📦 Perf report: $OUTHTML"
  # Optional (nice for WSL users): also print Windows UNC path if available
  if command -v wslpath >/dev/null 2>&1; then
    WINPATH="$(wslpath -w "$(pwd)/$OUTHTML" 2>/dev/null || true)"
    [[ -n "${WINPATH:-}" ]] && echo "📂 Windows path: $WINPATH"
  fi
  echo "🎉 Testing complete!"
fi