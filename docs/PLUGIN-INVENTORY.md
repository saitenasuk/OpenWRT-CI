# 当前插件清单（已确认配置）

核对日期：2026-11-13。构建目标仅 `jdcloud_re-ss-01`，配置 `IPQ60XX-WIFI-NO`，默认 LAN 地址 `10.1.1.1`。

**这是当前配置的静态清单，不是已经编译成功的镜像 manifest，也不是路由器现有安装包清单。** 主源码和 feeds 尚未锁定；最终包集合会受默认包、依赖和 `make defconfig` 影响。用户选择已写入 `Config/PRIVATE.txt`，最终以成功的配置检查和镜像 manifest 为准。

## 1. 最终请求的 11 个应用

来源：`Config/GENERAL.txt` 后叠加 `Config/PRIVATE.txt`。尚未执行真实整机 `make defconfig` / 编译。

| 软件包 | 用途 | 状态 |
|---|---|---|
| `luci-app-autoreboot` | 定时重启 | 保留 |
| `luci-app-mini-diskmanager` | 磁盘 / 分区管理 | 保留 |
| `luci-app-natmapt` | NATMap 端口映射 | 保留 |
| `luci-app-partexp` | 分区扩容 / 挂载 | 保留 |
| `luci-app-upnp` | UPnP 端口映射 | 保留 |
| `luci-app-wolultra` | 网络唤醒 | 保留 |
| `luci-app-openclash` | 代理 / 分流，配置请求内置 Mihomo 核心 | 添加，默认关闭 |
| `luci-app-easytier` | EasyTier 组网，显式选择 easytier 核心 | 添加，默认关闭 |
| `luci-app-netspeedtest` | 网络测速，使用 iperf3-ssl 避免普通版冲突 | 添加 |
| `luci-app-netbird` | NetBird 组网，显式选择 netbird 和运行时依赖 | 添加，默认关闭 |
| `luci-app-tailscale` | whzhni1 版管理界面，刷机后由插件下载核心 | 添加，默认关闭 |

## 2. 主题、管理界面和源码默认包

- 两个工作流均选择 `WRT_THEME: vantage`。`Scripts/Settings.sh` 选择 `luci`、简体中文、`luci-theme-vantage` 和 `luci-app-vantage`（仪表盘）。
- 脚本还拼接 `luci-app-vantage-config`，但本次检查的主题源码未找到该包；不要把这行当成已存在的独立插件，需以最终解析结果为准。
- 当前 LuCI 集合依赖带入 `luci-app-firewall`（防火墙）和 `luci-app-package-manager`（软件包管理），以及基础管理模块。
- 当前 `VIKINGYFY/immortalwrt` 的 `target/linux/qualcommax/Makefile` 默认选择 `luci-app-qca-ppe-qos`（高通 PPE QoS 管理）；最终是否保留及设备实际效果需另行验证。
- `cpufreq` 在通用配置中选中的是 CPU 调频工具，不等同于已经选中 `luci-app-cpufreq` 页面。
- `kmod-wireguard` 代表 WireGuard 内核模块，不等于完整 VPN 管理插件已配置。

上述远程源码是在核对日期读取的，后续滚动构建可能变化。

## 3. 显式关闭的应用与专用服务

- `luci-app-homeproxy`、`sing-box`
- `luci-app-gecoosac`、`gecoosac`
- `luci-app-samba4`、`samba4-server`、`samba4-client`
- feeds 的 `tailscale` / `tailscaled`：避免与 whzhni1 插件自己的配置、服务文件冲突。
- 普通 `iperf3`：改为测速包依赖的 `iperf3-ssl`。

- `luci-app-attendedsysupgrade`
- `luci-app-wol`

`luci-app-wol` 是基础网络唤醒页面；当前改用 WOL Ultra。`luci-app-attendedsysupgrade` 是 Attended Sysupgrade 管理页面。

## 4. 完整的显式基础组件选择

以下是上游 `GENERAL.txt` 的基础组件清单，不是最终镜像 manifest。`PRIVATE.txt` 已将 `iperf3` 替换为 `iperf3-ssl`，并显式补入 NetBird、conntrack、rpcd/ucode 等依赖。

```text
autocore
automount
blkid
cfdisk
cgdisk
coremark
cpufreq
curl
dmesg
exfat-fsck
exfat-mkfs
fdisk
fullconenat-sonic
gdisk
htop
iperf3
ip-full
libimobiledevice
libnvme
lsblk
luci-base
luci-compat
luci-lib-base
luci-lib-ipkg
luci-lua-runtime
luci-proto-relay
mmc-utils
nand-utils
nvme-cli
openssh-keygen
openssh-sftp-server
openssl-util
proto-bonding
sfdisk
sgdisk
smartmontools
smartmontools-drivedb
stuntman-client
usb-modeswitch
usbmuxd
usbutils
xz-utils
```

## 5. 完整的显式内核模块选择

```text
kmod-ata-ahci
kmod-ata-core
kmod-bonding
kmod-dsa
kmod-dummy
kmod-fs-btrfs
kmod-fs-ksmbd
kmod-fuse
kmod-inet-diag
kmod-inet-mptcp-diag
kmod-mtd-rw
kmod-netlink-diag
kmod-nf-nat
kmod-nf-nat6
kmod-nft-arp
kmod-nft-bridge
kmod-nft-connlimit
kmod-nft-core
kmod-nft-dup-inet
kmod-nft-fib
kmod-nft-nat
kmod-nft-netdev
kmod-nft-offload
kmod-nft-queue
kmod-nft-socket
kmod-nft-tproxy
kmod-nft-xfrm
kmod-nvme
kmod-ovpn-backports
kmod-sound-core
kmod-tun
kmod-usb3
kmod-usb-audio
kmod-usb-core
kmod-usb-dwc3
kmod-usb-ehci
kmod-usb-net
kmod-usb-net-asix
kmod-usb-net-asix-ax88179
kmod-usb-net-cdc-eem
kmod-usb-net-cdc-ether
kmod-usb-net-cdc-mbim
kmod-usb-net-cdc-ncm
kmod-usb-net-cdc-subset
kmod-usb-net-huawei-cdc-ncm
kmod-usb-net-ipheth
kmod-usb-net-rndis
kmod-usb-net-rtl8150
kmod-usb-net-rtl8152
kmod-usb-net-sierrawireless
kmod-usb-ohci
kmod-usb-storage
kmod-usb-storage-extras
kmod-usb-storage-uas
kmod-usb-uhci
kmod-veth
kmod-wireguard
```

## 6. 当前准备的额外源码

只拉取已选应用 / 主题和必要依赖；未选的代理、QModem、下载器和主题不再参与包扫描。这不限制以后按需添加，但新增前需重新核对依赖。

| 脚本匹配名 | 仓库 | 分支 |
|---|---|---|
| `vantage` | `anothaDev/luci-theme-vantage` | `main` |
| `openclash` | `vernesong/OpenClash` | `dev` |
| `diskmanager` | `4IceG/luci-app-mini-diskmanager` | `main` |
| `easytier` | `EasyTier/luci-app-easytier` | `main` |
| `viking` | `VIKINGYFY/packages` | `main` |
| `netspeedtest` | `sirpdboy/netspeedtest` | `main` |
| `partexp` | `sirpdboy/luci-app-partexp` | `main` |
| `natmapt` | `muink/openwrt-natmapt` | `master` |
| `stuntman` | `muink/openwrt-stuntman` | `master` |
| `luci-app-natmapt` | `muink/luci-app-natmapt` | `master` |

NetBird 和 whzhni1 Tailscale 由 `Scripts/PRIVATE.sh` 另行固定提交引入。

## 7. 配置计数及下一步

`GENERAL.txt` 当前显式选择 108 个软件包：9 个应用、57 个内核模块、42 个其他组件。这不是最终镜像包总数。

应用选择已经确认；请先运行配置检查，再编译。NetBird / Tailscale 新源码由 `Scripts/PRIVATE.sh` 引入并固定提交；本清单本身不参与编译。

核对来源：本地 `Config/GENERAL.txt`、`Scripts/Packages.sh`、`Scripts/Settings.sh`；远程源码 `VIKINGYFY/immortalwrt` 的平台默认配置及 `package/emortal/`，`immortalwrt/luci` 的 `collections/luci` 与 `collections/luci-light`，`VIKINGYFY/packages`（本次核对提交 `c0408ae`），以及相关插件作者仓库的 Makefile/README。

## 8. 新增源码与兼容修补

- OpenClash：修正内置核心编译宏的 shell 变量转义（`$$CORE_ARCH` → `$$$$CORE_ARCH`），避免构造 `clash-ORE_ARCH.tar.gz` 错误地址；未改变渠道或版本策略。

- NetBird：`looong-cat/luci-app-netbird`，提交 `de70650ff79abd24b114c045473cf16f118a3957`。
- Tailscale：`whzhni1/luci-app-tailscale`，提交 `1274256218dd1b638a183a0e5b2bef5df17eb8d2`。
- Tailscale：移除当前源码不存在且后端未使用的 `ucode-mod-html` 依赖；将包生命周期钩子放到 `luci.mk` include 前，避免重复 BuildPackage，同时保留包扫描标识。
- 网络测速：移除当前软件源已不提供、脚本也没有导入的 `python3-pkg-resources` 旧依赖；将旧 `python3-email` 名称移除，email 模块仍由已有 `python3-urllib` 依赖提供；固定依赖 `iperf3-ssl`，不再使用上游错误的探测表达式。
- NetBird：显式带入上游 EXTRA_DEPENDS 中的整机编译依赖；默认关闭服务、LAN 转发、远端子网路由，并为核心 init 的 boot 动作增加主开关检查。
- Tailscale：保留原有关闭状态、关闭 DNS / 路由接受与自动核心升级，并关闭预设的双向 LAN 转发；用户启用后可按需打开。
- EasyTier / OpenClash：验证源配置中的总开关默认为关闭；EasyTier 地址和掩码尚未设置，启用前必须规划。
