#!/bin/bash
# Sourced by Packages.sh while the working directory is the firmware source root.
# Only the two newly integrated LuCI sources are pinned here; this is not a full lock.
set -euo pipefail

add_pinned_luci() {
    local name="$1" repo="$2" commit="$3"
    local dest="package/$name" feed
    test -d package && test -d feeds/luci && test -d feeds/packages
    if [ -e "$dest" ]; then
        echo "Refusing to overwrite existing custom source: $dest" >&2
        return 1
    fi
    # Remove only the matching LuCI app; retain the netbird core feed package.
    for feed in luci packages; do
        find "feeds/$feed" -type d -name "$name" -prune -exec rm -rf {} +
        rm -f "package/feeds/$feed/$name"
    done
    git init -q "$dest"
    git -C "$dest" remote add origin "https://github.com/$repo.git"
    git -C "$dest" fetch --depth=1 origin "$commit"
    git -C "$dest" -c advice.detachedHead=false checkout --detach FETCH_HEAD
    test "$(git -C "$dest" rev-parse HEAD)" = "$commit"
    test -f "$dest/$name/Makefile"
    printf '%s %s %s\n' "$name" "$repo" "$commit" >> "$REPORT_DIR/custom-sources.txt"
}

REPORT_DIR="$GITHUB_WORKSPACE/build-reports"
mkdir -p "$REPORT_DIR"
: > "$REPORT_DIR/custom-sources.txt"
add_pinned_luci luci-app-netbird looong-cat/luci-app-netbird de70650ff79abd24b114c045473cf16f118a3957
add_pinned_luci luci-app-tailscale whzhni1/luci-app-tailscale 1274256218dd1b638a183a0e5b2bef5df17eb8d2
python3 "$GITHUB_WORKSPACE/Scripts/customize-vpn-packages.py" .
