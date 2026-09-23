#!/usr/bin/env bash
# Does Nave's frozen C-extension set still compile?
#
# These five pins have no wheels on PyPI at cp39 for any architecture, so
# they build from source against the system libraries the shell provides.
# That is the riskiest assumption behind running Nave on NixOS, and this
# script is the cheapest way to settle it. Run it inside `nix develop`.
set -uo pipefail

VENV="${1:-/tmp/nave-ext-check}"

PINS=(
  "lxml==4.4.2"
  "pyproj==2.6.1"
  "shapely==1.5.17"
  "psycopg2==2.8.4"
  "protobuf==3.11.3"
)

# Import name differs from the distribution name for two of them.
declare -A IMPORTS=(
  ["lxml==4.4.2"]="lxml.etree"
  ["pyproj==2.6.1"]="pyproj"
  ["shapely==1.5.17"]="shapely.geos"
  ["psycopg2==2.8.4"]="psycopg2"
  ["protobuf==3.11.3"]="google.protobuf"
)

echo "=== environment ==="
python3 --version
echo "PROJ_DIR=${PROJ_DIR:-unset}"
echo "GEOS_CONFIG=${GEOS_CONFIG:-unset}"
pg_config --version 2>/dev/null || echo "pg_config: MISSING"
echo

rm -rf "$VENV"
python3 -m venv "$VENV" || exit 1
# shellcheck disable=SC1091
source "$VENV/bin/activate"

# The build environment has to be as old as what it is building. pip's
# default isolated build env installs a current setuptools, where
# pkg_resources is gone -- pyproj 2.6.1's setup.py imports it and dies. So
# pin the build tools here and build with --no-build-isolation instead.
# Cython is pinned below 3 because pyproj 2.6.1 predates the Cython 3 syntax.
python3 -m pip install --quiet --upgrade "pip<24" "setuptools<60" wheel "cython<3" 2>&1 | tail -3

declare -A BUILD_RESULT
declare -A IMPORT_RESULT

for pin in "${PINS[@]}"; do
  echo "=== building $pin ==="
  if python3 -m pip install --no-build-isolation --no-cache-dir "$pin" > "/tmp/nave-ext-${pin%%=*}.log" 2>&1; then
    BUILD_RESULT[$pin]="ok"
    echo "  build ok"
  else
    BUILD_RESULT[$pin]="FAIL"
    echo "  build FAILED — tail of /tmp/nave-ext-${pin%%=*}.log:"
    tail -15 "/tmp/nave-ext-${pin%%=*}.log" | sed 's/^/    /'
    continue
  fi

  # Building is not enough: shapely and filemagic dlopen their library at
  # import time, so a successful compile can still fail on first use.
  mod="${IMPORTS[$pin]}"
  if python3 -c "import $mod" 2>"/tmp/nave-import-${pin%%=*}.log"; then
    IMPORT_RESULT[$pin]="ok"
    echo "  import ok"
  else
    IMPORT_RESULT[$pin]="FAIL"
    echo "  import FAILED:"
    sed 's/^/    /' "/tmp/nave-import-${pin%%=*}.log" | tail -8
  fi
done

echo
echo "=== summary ==="
failed=0
for pin in "${PINS[@]}"; do
  b="${BUILD_RESULT[$pin]:-skipped}"
  i="${IMPORT_RESULT[$pin]:-skipped}"
  printf '  %-22s build=%-6s import=%s\n' "$pin" "$b" "$i"
  [[ "$b" == "ok" && "$i" == "ok" ]] || failed=1
done

if [[ $failed -eq 0 ]]; then
  echo
  echo "ALL FIVE BUILD AND IMPORT — the nixos-21.05 pin holds."
else
  echo
  echo "AT LEAST ONE FAILED — see the logs named above."
fi
exit $failed
