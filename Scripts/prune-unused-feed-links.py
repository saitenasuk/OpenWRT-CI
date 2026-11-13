#!/usr/bin/env python3
"""Exclude confirmed unused, broken package definitions from metadata scanning.

Only unlink installed feed entries. Preserve the source repositories for review,
never modify the definitions of a selected package to hide a dependency error.
"""
from pathlib import Path
import sys

EXCLUDED_SOURCES = ('feeds/luci/applications/luci-app-fwknopd',
                    'feeds/packages/sound/squeezelite')


def prune(root):
    excluded = [root / name for name in EXCLUDED_SOURCES]
    removed = []
    installed = root / 'package/feeds'
    for feed in installed.iterdir():
        if not feed.is_dir():
            continue
        for entry in feed.iterdir():
            if not entry.is_symlink():
                continue
            target = entry.resolve()
            if any(target == path or path in target.parents for path in excluded):
                entry.unlink()
                removed.append(str(entry.relative_to(root)))
    print('Unused feed links removed: ' + (', '.join(removed) or 'none'))


if __name__ == '__main__':
    prune(Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve())
