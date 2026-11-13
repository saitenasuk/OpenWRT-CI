#!/usr/bin/env python3
"""Apply narrow, checked integration fixes to the selected VPN package sources."""
from pathlib import Path
import re
import sys


def replace_once(path, old, new):
    text = path.read_text()
    if old not in text and new in text:
        return
    if text.count(old) != 1:
        raise RuntimeError(f"Upstream changed: expected one matching block in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1))


def set_option(path, key, old, new):
    replace_once(path, f"option {key} '{old}'", f"option {key} '{new}'")


def customize(root):
    netbird = root / 'package/luci-app-netbird/luci-app-netbird'
    tailscale = root / 'package/luci-app-tailscale/luci-app-tailscale'
    easytier = root / 'package/luci-app-easytier/luci-app-easytier'
    for package in (netbird, tailscale, easytier):
        if not (package / 'Makefile').is_file():
            raise RuntimeError(f"Missing package source: {package}")

    # The current firmware has no ucode-mod-html package; this pinned backend
    # imports fs and uci, not html. Stop rather than silently dropping a used module.
    for path in (tailscale / 'root').rglob('*'):
        if path.is_file():
            code = path.read_text(errors='replace')
            if re.search(r"(?:from\s+|require\(\s*|import\s*)['\"]html['\"]", code):
                raise RuntimeError(f'Unexpected html module usage: {path}')
    makefile = tailscale / 'Makefile'
    text = makefile.read_text()
    if '+ucode-mod-html' in text:
        text = text.replace(' +ucode-mod-html', '')
    # luci.mk already registers BuildPackage. Keep lifecycle hooks before its
    # single include instead of registering the package twice.
    include = 'include $(TOPDIR)/feeds/luci/luci.mk'
    registration = '$(eval $(call BuildPackage,$(PKG_NAME)))'
    if text.count(include) != 1:
        raise RuntimeError('Unexpected Tailscale luci.mk include layout')
    text = text.replace(include, '').replace(registration, '').rstrip()
    signature = '# call BuildPackage - OpenWrt buildroot signature'
    text = text.replace(signature, '').rstrip()
    makefile.write_text(text + '\n\n' + include + '\n\n' + signature + '\n')

    # Current setuptools no longer provides python3-pkg-resources. This bundled
    # speedtest script never imports it; retain the other Python dependencies.
    speedtest = root / 'package/netspeedtest/luci-app-netspeedtest'
    for path in (speedtest / 'root').rglob('*'):
        if path.is_file():
            code = path.read_text(errors='replace')
            if 'pkg_resources' in code:
                raise RuntimeError(f'Unexpected pkg_resources usage: {path}')
    speed_mk = speedtest / 'Makefile'
    speed_mk.write_text(speed_mk.read_text().replace(' +python3-pkg-resources', ''))

    # Fresh installs must not enroll, export the LAN or import remote routes.
    netbird_configs = [netbird / 'root/etc/config/netbird',
                       netbird / 'root/usr/share/luci-app-netbird/defaults/netbird.uci']
    for path in netbird_configs:
        for key in ('service_enabled', 'access_lan', 'accept_client_routes', 'accept_server_routes'):
            set_option(path, key, '1', '0')
    defaults = netbird / 'root/etc/uci-defaults/99-luci-app-netbird'
    for key in ('service_enabled', 'access_lan', 'accept_client_routes', 'accept_server_routes'):
        replace_once(defaults, f'_set_if_missing {key} 1', f'_set_if_missing {key} 0')

    # Upstream netbird.init starts the daemon unconditionally at boot. Preserve
    # manual starts from the UI, but gate only boot on this plugin's master switch.
    init = root / 'feeds/packages/net/netbird/files/netbird.init'
    marker = '# arthur-netbird-boot-guard'
    if marker not in init.read_text():
        replace_once(init, 'start_service() {', '''# arthur-netbird-boot-guard
boot() {
	[ "$(uci -q get netbird.settings.service_enabled)" = "1" ] || return 0
	start "$@"
}

start_service() {''')

    ts_config = tailscale / 'root/etc/config/tailscale'
    for key in ('fwd_ts_lan', 'fwd_lan_ts'):
        set_option(ts_config, key, '1', '0')
    # These switches are already off in the pinned sources: verify, don't guess.
    checks = [
        (ts_config, "option enabled '0'"),
        (ts_config, "option accept_dns '0'"),
        (ts_config, "option accept_routes '0'"),
        (ts_config, "option auto_update '0'"),
        (easytier / 'root/etc/config/easytier', "option enabled '0'"),
        (root / 'package/luci-app-openclash/root/etc/config/openclash', "option enable '0'"),
    ]
    for path, token in checks:
        if token not in path.read_text():
            raise RuntimeError(f'Expected disabled-by-default setting missing: {path}: {token}')
    print('VPN package integration checked; VPN/proxy services remain disabled by default.')


if __name__ == '__main__':
    customize(Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve())
