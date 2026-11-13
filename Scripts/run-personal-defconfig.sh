#!/bin/bash
# Run from the firmware source root; retain evidence even when Kconfig fails.
set -euo pipefail
: "${GITHUB_WORKSPACE:?Set GITHUB_WORKSPACE to the CI configuration repository}"
REPORT_DIR="$GITHUB_WORKSPACE/build-reports"
mkdir -p "$REPORT_DIR"
trap 'if [ -f .config ]; then cp .config "$REPORT_DIR/config.txt"; fi' EXIT
make defconfig -j"$(nproc)" 2>&1 | tee "$REPORT_DIR/defconfig.log"
# Some Kconfig versions write .config despite recursive dependency diagnostics.
# Never accept that partially resolved configuration just because make returned 0.
if grep -q 'recursive dependency detected!' "$REPORT_DIR/defconfig.log"; then
    echo 'Kconfig contains recursive dependencies; see build-reports/defconfig.log.' >&2
    exit 1
fi
python3 "$GITHUB_WORKSPACE/Scripts/check-personal-config.py" \
    .config "$GITHUB_WORKSPACE/Config/PRIVATE.txt" 2>&1 | tee "$REPORT_DIR/config-validation.log"
