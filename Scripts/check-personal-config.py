#!/usr/bin/env python3
"""Fail CI if Kconfig drops requested packages or restores excluded packages."""
from pathlib import Path
import re
import sys


def parse_config(path):
    values = {}
    for line in Path(path).read_text().splitlines():
        match = re.fullmatch(r'(CONFIG_[A-Za-z0-9_+.-]+)=(.*)', line)
        if match:
            values[match[1]] = match[2]
        else:
            match = re.fullmatch(r'# (CONFIG_[A-Za-z0-9_+.-]+) is not set', line)
            if match:
                values[match[1]] = 'n'
    return values


def validate(actual_path, requested_path):
    actual, requested = parse_config(actual_path), parse_config(requested_path)
    errors = []
    for symbol, wanted in requested.items():
        if wanted in ('y', 'm') and actual.get(symbol) != wanted:
            errors.append(f'{symbol}: expected {wanted}, got {actual.get(symbol, "missing")}')
        elif wanted == 'n' and actual.get(symbol, 'n') != 'n':
            errors.append(f'{symbol}: requested disabled, got {actual[symbol]}')
    selected = {k for k, v in actual.items() if k.startswith('CONFIG_TARGET_DEVICE_') and v == 'y'}
    device = 'CONFIG_TARGET_DEVICE_qualcommax_ipq60xx_DEVICE_jdcloud_re-ss-01'
    if selected != {device}:
        errors.append(f'Unexpected selected device set: {sorted(selected)}')
    for symbol in ('CONFIG_TARGET_qualcommax', 'CONFIG_TARGET_qualcommax_ipq60xx'):
        if actual.get(symbol) != 'y':
            errors.append(f'Missing target: {symbol}')
    if errors:
        raise RuntimeError('Personal firmware config validation failed:\n' + '\n'.join(errors))
    print(f'Personal configuration validated: {len(requested)} overrides and only RE-SS-01.')


if __name__ == '__main__':
    validate(sys.argv[1], sys.argv[2])
