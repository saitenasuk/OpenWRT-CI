#!/usr/bin/env python3
"""Omit disabled feeds before update/install, instead of only setting FEED_*=n."""
from pathlib import Path
import sys

DISABLED_FEEDS = {'video', 'pon_drivers', 'pon_userspace'}


def prepare(root):
    path = root / 'feeds.conf'
    if not path.exists():
        path = root / 'feeds.conf.default'
    result, removed = [], []
    for line in path.read_text().splitlines(keepends=True):
        tokens = line.split()
        if len(tokens) >= 2 and tokens[0].startswith('src-') and tokens[1] in DISABLED_FEEDS:
            removed.append(tokens[1])
        else:
            result.append(line)
    path.write_text(''.join(result))
    print(f'Personal feeds: excluded {", ".join(removed) or "none (already filtered)"}')


if __name__ == '__main__':
    prepare(Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve())
