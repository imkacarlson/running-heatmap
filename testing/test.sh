#!/usr/bin/env bash
set -euo pipefail

PERF_MODE="none"
ARGS=()

# Parse --perf and optional mode (pyi|scalene)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --perf)           PERF_MODE="pyi"; shift ;;
    --perf=pyi)       PERF_MODE="pyi"; shift ;;
    --perf=scalene)   PERF_MODE="scalene"; shift ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
set -- "${ARGS[@]}"

echo "🧪 Activity Heatmap Mobile App Tests"
echo "============================================"

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source test_venv/bin/activate

STAMP=$(date +%Y%m%d-%H%M%S)
BASE="reports/perf"
OUTDIR="$BASE/${PERF_MODE}-${STAMP}"
mkdir -p "$OUTDIR"

run_pytest() {
  # Run the enhanced test suite
  echo "🚀 Running tests with enhanced runner..."
  python run_tests.py "$@"
}

case "$PERF_MODE" in
  none)
    run_pytest "$@"
    echo "🎉 Testing complete!"
    ;;
  pyi)
    if ! python -c "import pyinstrument" >/dev/null 2>&1; then
      echo "Missing dependency: pyinstrument (pip install -r testing/requirements.txt)" >&2; exit 2
    fi
    OUTHTML="$OUTDIR/profile.html"
    # one HTML flamegraph for the whole run
    echo "🔥 Running tests with PyInstrument profiling..."
    python -m pyinstrument -r html -o "$OUTHTML" -m run_tests "$@"
    echo "📦 Perf report (PyInstrument): $OUTHTML"
    ;;
  scalene)
    if ! python -c "import scalene" >/dev/null 2>&1; then
      echo "Missing dependency: scalene (pip install -r testing/requirements.txt)" >&2; exit 2
    fi
    export PERF_OUTDIR="$OUTDIR"   # optional: so your step timers write next to the report
    OUTHTML="$OUTDIR/scalene.html"
    # per-line CPU/memory report for the whole run
    echo "🔥 Running tests with Scalene profiling..."
    python -m scalene --html --outfile "$OUTHTML" --profile-all --profile-exclude 'subprocess.*' --profile-exclude 'threading.*' -m run_tests "$@"
    echo "📦 Perf report (Scalene): $OUTHTML"
    ;;
  *)
    echo "unknown --perf mode: $PERF_MODE" >&2; exit 2
    ;;
esac

# (Optional) nice-to-have for WSL
if command -v wslpath >/dev/null 2>&1; then
  WINPATH="$(wslpath -w "$(pwd)/$OUTDIR" 2>/dev/null || true)"
  [[ -n "${WINPATH:-}" ]] && echo "📂 Windows folder: $WINPATH"
fi