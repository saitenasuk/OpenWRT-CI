"""Offline regression checks; run python3 -m unittest discover -s tests -v."""
from contextlib import redirect_stdout
import importlib.util
from io import StringIO
from pathlib import Path
import tempfile
import os
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'Scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check = load('personal_config', 'check-personal-config.py')
patch = load('vpn_packages', 'customize-vpn-packages.py')
feeds = load('personal_feeds', 'prepare-personal-feeds.py')
prune = load('feed_links', 'prune-unused-feed-links.py')


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.requested = ROOT / 'Config/PRIVATE.txt'
        self.values = check.parse_config(self.requested)
        self.values.update({
            'CONFIG_TARGET_qualcommax': 'y',
            'CONFIG_TARGET_qualcommax_ipq60xx': 'y',
            'CONFIG_TARGET_DEVICE_qualcommax_ipq60xx_DEVICE_jdcloud_re-ss-01': 'y',
        })

    def run_check(self):
        path = self.root / '.config'
        path.write_text('\n'.join(f'# {k} is not set' if v == 'n' else f'{k}={v}'
                                  for k, v in self.values.items()))
        with redirect_stdout(StringIO()):
            check.validate(path, self.requested)

    def test_expected_config(self):
        self.run_check()

    def test_missing_requested_plugin(self):
        del self.values['CONFIG_PACKAGE_luci-app-netbird']
        with self.assertRaisesRegex(RuntimeError, 'luci-app-netbird'):
            self.run_check()

    def test_unwanted_dependency_returns(self):
        self.values['CONFIG_PACKAGE_samba4-server'] = 'y'
        with self.assertRaisesRegex(RuntimeError, 'samba4-server'):
            self.run_check()

    def test_other_device_is_rejected(self):
        self.values['CONFIG_TARGET_DEVICE_qualcommax_ipq60xx_DEVICE_other'] = 'y'
        with self.assertRaisesRegex(RuntimeError, 'Unexpected selected device'):
            self.run_check()

    def test_missing_disabled_virtual_package_is_ok(self):
        del self.values['CONFIG_PACKAGE_tailscaled']
        self.run_check()


class PackagePatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.nb = 'package/luci-app-netbird/luci-app-netbird'
        self.ts = 'package/luci-app-tailscale/luci-app-tailscale'
        self.et = 'package/luci-app-easytier/luci-app-easytier'
        for folder in (self.nb, self.ts, self.et):
            self.write(folder + '/Makefile', 'include $(TOPDIR)/rules.mk\n')
        self.write(self.ts + '/Makefile', '''PKG_NAME:=luci-app-tailscale
LUCI_DEPENDS:=+luci-base +ucode-mod-html +curl
include $(TOPDIR)/feeds/luci/luci.mk

define Package/$(PKG_NAME)/postinst
exit 0
endef
$(eval $(call BuildPackage,$(PKG_NAME)))
''')
        nb_keys = ('service_enabled', 'access_lan', 'accept_client_routes', 'accept_server_routes')
        config = '\n'.join(f"option {key} '1'" for key in nb_keys)
        self.write(self.nb + '/root/etc/config/netbird', config)
        self.write(self.nb + '/root/usr/share/luci-app-netbird/defaults/netbird.uci', config)
        self.write(self.nb + '/root/etc/uci-defaults/99-luci-app-netbird',
                   '\n'.join(f'_set_if_missing {key} 1' for key in nb_keys))
        self.write('feeds/packages/net/netbird/files/netbird.init',
                   'start_service() {\n\tprocd_open_instance\n}\n')
        self.write(self.ts + '/root/etc/config/tailscale', '''option enabled '0'
option accept_dns '0'
option accept_routes '0'
option auto_update '0'
option fwd_ts_lan '1'
option fwd_lan_ts '1'
''')
        self.write(self.et + '/root/etc/config/easytier', "option enabled '0'\n")
        self.write('package/luci-app-openclash/root/etc/config/openclash', "option enable '0'\n")
        self.write('package/netspeedtest/luci-app-netspeedtest/Makefile',
                   'LUCI_DEPENDS:=+python3-light +python3-pkg-resources +python3-email +python3-urllib $(if $(find_package iperf3-ssl),+iperf3-ssl,+iperf3)\n')
        self.write('package/netspeedtest/luci-app-netspeedtest/root/usr/bin/speedtest', 'import csv\n')

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def run_patch(self):
        with redirect_stdout(StringIO()):
            patch.customize(self.root)

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def test_patches_are_idempotent_and_hooks_precede_include(self):
        self.run_patch()
        before = self.snapshot()
        self.run_patch()
        self.assertEqual(before, self.snapshot())
        mk = (self.root / self.ts / 'Makefile').read_text()
        self.assertNotIn('ucode-mod-html', mk)
        self.assertNotIn('$(call BuildPackage', mk)
        self.assertIn('# call BuildPackage - OpenWrt buildroot signature', mk)
        self.assertNotIn('python3-pkg-resources', (self.root / 'package/netspeedtest/luci-app-netspeedtest/Makefile').read_text())
        speed_mk = (self.root / 'package/netspeedtest/luci-app-netspeedtest/Makefile').read_text()
        self.assertNotIn('+python3-email', speed_mk)
        self.assertIn('+python3-urllib', speed_mk)
        self.assertIn('+iperf3-ssl', speed_mk)
        self.assertNotIn('find_package', speed_mk)
        self.assertLess(mk.index('/postinst'), mk.index('include $(TOPDIR)/feeds/luci/luci.mk'))
        init = (self.root / 'feeds/packages/net/netbird/files/netbird.init').read_text()
        self.assertEqual(init.count('# arthur-netbird-boot-guard'), 1)
        self.assertIn("option service_enabled '0'", (self.root / self.nb / 'root/etc/config/netbird').read_text())

    def test_real_html_usage_is_not_silently_removed(self):
        self.write(self.ts + '/root/usr/libexec/rpcd/tailscale', "import { encode } from 'html';")
        with self.assertRaisesRegex(RuntimeError, 'Unexpected html module usage'):
            self.run_patch()

    def test_changed_source_layout_fails_loudly(self):
        self.write(self.nb + '/root/etc/config/netbird', '# incompatible new schema')
        with self.assertRaisesRegex(RuntimeError, 'Upstream changed'):
            self.run_patch()


class FeedScopeTests(unittest.TestCase):
    def test_disabled_feeds_are_filtered_before_install(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = root / 'feeds.conf.default'
            p.write_text('src-git packages https://example.test/packages.git\n'
                         'src-git luci https://example.test/luci.git\n'
                         'src-git video https://example.test/video.git\n'
                         'src-git pon_drivers https://example.test/pon.git\n'
                         '#src-git video https://example.test/comment.git\n')
            with redirect_stdout(StringIO()):
                feeds.prepare(root)
                result = p.read_text()
                feeds.prepare(root)
            self.assertEqual(p.read_text(), result)
            self.assertIn('src-git packages ', result)
            self.assertIn('src-git luci ', result)
            self.assertNotIn('\nsrc-git video ', result)
            self.assertNotIn('\nsrc-git pon_drivers ', result)
            self.assertIn('#src-git video ', result)

    def test_prune_only_targeted_feed_symlinks_not_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for src in prune.EXCLUDED_SOURCES + ('feeds/packages/net/iperf3',):
                target = root / src
                target.mkdir(parents=True)
                (target / 'Makefile').write_text('# preserved source')
                feed = src.split('/')[1]
                link = root / 'package/feeds' / feed / target.name
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(target, target_is_directory=True)
            with redirect_stdout(StringIO()):
                prune.prune(root)
                prune.prune(root)
            for src in prune.EXCLUDED_SOURCES:
                self.assertTrue((root / src / 'Makefile').is_file())
                self.assertFalse((root / 'package/feeds' / src.split('/')[1] / Path(src).name).is_symlink())
            self.assertTrue((root / 'package/feeds/packages/iperf3').is_symlink())

    def test_custom_sources_exclude_unused_circular_definitions(self):
        import shlex
        sources = [shlex.split(line)[1] for line in (ROOT / 'Scripts/Packages.sh').read_text().splitlines()
                   if line.startswith('UPDATE_PACKAGE ')]
        self.assertEqual(set(sources), {'vantage', 'openclash', 'diskmanager', 'easytier',
                                       'viking', 'netspeedtest', 'partexp', 'natmapt',
                                       'stuntman', 'luci-app-natmapt'})


class DefconfigLogTests(unittest.TestCase):
    def test_recursive_diagnostic_is_fatal_even_when_make_returns_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            make = bin_dir / 'make'
            make.write_text('#!/bin/sh\necho "sample: error: recursive dependency detected!"\n'
                            'printf "CONFIG_TEST=y\\n" > .config\nexit 0\n')
            make.chmod(0o755)
            env = dict(os.environ, PATH=str(bin_dir) + ':' + os.environ['PATH'],
                       GITHUB_WORKSPACE=str(root))
            proc = subprocess.run(['bash', str(ROOT / 'Scripts/run-personal-defconfig.sh')],
                                  cwd=root, env=env, capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('Kconfig contains recursive dependencies', proc.stderr)
            self.assertTrue((root / 'build-reports/defconfig.log').is_file())
            self.assertEqual((root / 'build-reports/config.txt').read_text(), 'CONFIG_TEST=y\n')

    def test_speedtest_make_expression_selects_ssl_after_patch(self):
        with tempfile.TemporaryDirectory() as temp:
            # Match the dependency syntax used by the real package metadata scanner.
            p = Path(temp) / 'Makefile'
            p.write_text('DEPS:=+python3-urllib +iperf3-ssl\nall:;@echo "$(DEPS)"\n')
            result = subprocess.check_output(['make', '-s', '-f', str(p)], text=True).strip().split()
            self.assertIn('+iperf3-ssl', result)
            self.assertNotIn('+iperf3', result)


if __name__ == '__main__':
    unittest.main()
