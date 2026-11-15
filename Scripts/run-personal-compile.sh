#!/bin/bash
# Retain both attempts without allowing tee to hide a failing make exit code.
set -euo pipefail
: "${GITHUB_WORKSPACE:?Set GITHUB_WORKSPACE to the CI configuration repository}"
REPORT_DIR="$GITHUB_WORKSPACE/build-reports"
mkdir -p "$REPORT_DIR"
if make -j"$(nproc)" BUILD_TIME_LOG="$REPORT_DIR/parallel.tsv" \
        2>&1 | tee "$REPORT_DIR/compile-parallel.log"; then
    exit 0
fi
printf '\nParallel compile failed; retrying serially with V=s.\n'
make -j1 V=s BUILD_TIME_LOG="$REPORT_DIR/serial.tsv" \
    2>&1 | tee "$REPORT_DIR/compile-serial.log"
