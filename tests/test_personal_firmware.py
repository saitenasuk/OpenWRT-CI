"""Offline regression checks; run python3 -m unittest discover -s tests -v."""
from contextlib import redirect_stdout
import importlib.util
from io import StringIO
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'Scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check = load('personal_config', 'check-personal-config.py')
patch = load('vpn_packages', 'customize-vpn-packages.py')


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
                   'LUCI_DEPENDS:=+python3-light +python3-pkg-resources +iperf3-ssl\n')
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


if __name__ == '__main__':
    unittest.main()
