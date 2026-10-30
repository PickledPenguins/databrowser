#!/bin/sh
# Run the tests.
#
#   tests/run-tests.sh                  the fast suite: unit, interface and smoke. Before a push.
#   tests/run-tests.sh long             the long suite: the example and failure catalogs,
#                                       properties, faults, concurrency, scaling, visual.
#   tests/run-tests.sh all              both. Before a release.
#   tests/run-tests.sh cov              the fast suite under coverage, failing under the floor.
#   tests/run-tests.sh perf             timing against this machine's baseline, then memory.
#   tests/run-tests.sh perf-baseline    record the timing baseline, .build/perf-baseline.json.
#   tests/run-tests.sh mutation         mutate the package and run the fast suite on each mutant.
#   tests/run-tests.sh visual           the screenshots against their goldens.
#   tests/run-tests.sh visual-update    rewrite the goldens, then review each changed image.
#   tests/run-tests.sh examples-update  rewrite the example catalog's expected pages, then review the diff.
#   tests/run-tests.sh ARGS...          anything else goes straight to pytest.
#
# PYTHON selects the interpreter, python3 by default. It needs pytest, and hypothesis and
# Pillow for the long suite, coverage for cov and mutmut for mutation. The visual tests
# need firefox and are skipped without it.
#
# Every generated file goes under .build/, except mutmut's mutants/, which it cannot move.

set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

PYTHON=${PYTHON:-python3}
# What the fast suite reaches, line and branch, so it gates a regression rather than
# describing an ambition. Never lower it to make a run pass.
FLOOR=100

export PYTHONPYCACHEPREFIX="$ROOT/.build/pycache"
mkdir -p .build

pytest() {
    "$PYTHON" -m pytest -q "$@"
}

case "${1:-fast}" in
fast)
    pytest -m "not long and not perf"
    ;;
long)
    pytest -m long
    ;;
all)
    pytest -m "not perf"
    ;;
cov)
    "$PYTHON" -m coverage erase
    "$PYTHON" -m coverage run -m pytest -q -m "not long and not perf"
    "$PYTHON" -m coverage report --fail-under="$FLOOR"
    "$PYTHON" -m coverage html
    echo "html report: .build/htmlcov/index.html"
    ;;
perf)
    # One process each: tracing allocations would slow the timed runs.
    pytest -p no:randomly -m perf -k test_time
    pytest -p no:randomly -m perf -k test_memory
    ;;
perf-baseline)
    PERF_RECORD=1 pytest -p no:randomly -m perf -k test_time
    echo "baseline: .build/perf-baseline.json"
    ;;
mutation)
    "$PYTHON" -m mutmut run
    "$PYTHON" -m mutmut results
    ;;
visual)
    pytest tests/test_visual.py
    ;;
visual-update)
    UPDATE_GOLDENS=1 pytest tests/test_visual.py
    git status --short tests/visual
    ;;
examples-update)
    UPDATE_EXPECTED=1 pytest tests/test_examples.py
    git status --short tests/examples
    ;;
*)
    pytest "$@"
    ;;
esac
