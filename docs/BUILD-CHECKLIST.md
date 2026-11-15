# 亚瑟构建与上线检查

## 已完成的本地配置

- 只构建 `jdcloud_re-ss-01` / `IPQ60XX-WIFI-NO`，默认 LAN `10.1.1.1`。
- 插件增删与依赖写入 `Config/PRIVATE.txt`；见 `PLUGIN-INVENTORY.md`。
- 两个新 LuCI 源码使用已检查提交；兼容修补和默认关闭策略由 `Scripts/PRIVATE.sh` 调用。
- `make defconfig` 后检查必需包、排除包、机型；不合格就终止 CI。
- 本地回归测试：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`。

这些不是完整固件编译、真机适配或组网吞吐测试的替代。

## 下一步 1：提交并推送

先检查 `git diff` 和新增文件；暂未替用户 commit / push。
必须包含 `Config/PRIVATE.txt`、`Scripts/PRIVATE.sh`、两个 Python 脚本、更新的工作流和文档。
检查没有账号密钥、代理订阅、NetBird setup key 或 Tailscale auth key，再提交并推送默认分支。

## 下一步 2：配置检查

Actions → `WRT-TEST` → Run workflow：

- CONFIG：`IPQ60XX-WIFI-NO`
- SOURCE：`VIKINGYFY/immortalwrt`
- BRANCH：`owrt`
- PACKAGE：留空
- TEST：`true`

此过程仍会准备源码和软件源，但不编译固件。关注日志中 `Personal configuration validated`。
缺包、依赖冲突、选项被取消应先修复，不要绕过检查。即使 `make defconfig` 返回成功，只要日志含循环依赖也会停止；失败后的 Actions Artifacts 中查看 `build-reports-*`，重点为 `defconfig.log`、`config.txt`、`config-validation.log`（若已执行）。生成的 `Config-...txt` 需包含 11 个应用、EasyTier / NetBird 核心、TUN / WireGuard 模块，且没有三个已删除应用及专用服务、普通 iperf3 和 feeds 的 Tailscale 包。

## 下一步 3：正式编译

配置检查通过后运行 `QCA-ALL`，`TEST=false`、PACKAGE 留空。构建时间、下载失败及编译问题以 Actions 日志为准。

OpenClash 当前选择在构建时获取 Mihomo 核心。EasyTier 与 NetBird 选择随镜像提供核心。
Tailscale 按 whzhni1 插件设计，在首次配置时使用插件的核心管理页面获取匹配 ARM64 的程序；它不是已经内置并离线可运行的 Tailscale 核心。未添加 GuNan 源。

保存亚瑟对应固件、manifest、最终配置、源码与 feeds 提交记录，以及 custom-sources 记录。
目前仅两个新 LuCI 源码固定提交；系统、feeds、其他插件和在线核心还不是完整锁定构建。候选版编译和真机测试通过后，再锁定验证过的全部输入，后续按需安排安全更新。

## 下一步 4：刷写前确认

先收集并人工核对以下只读信息：

```sh
ubus call system board
cat /etc/openwrt_release
uname -r
free -m
df -h
cat /proc/partitions
```

还需确认当前 U-Boot / eMMC 分区、已有救砖或回退路径。备份配置并下载到电脑，不上传含密码的备份。不能因为机型名称相同就假定跨年份升级兼容。
先连接有线 LAN；默认地址仅保证新配置的默认值，不承诺覆盖保留的旧网络配置。未在此项目中执行任何刷写命令。

## 下一步 5：逐个启用服务

先验证 WAN、LAN、DHCP、DNS、IPv6，再启用 OpenClash 或一个组网服务；不要首次启动就同时开三个组网工具。

- NetBird 和 Tailscale 均可能使用 `100.64.0.0/10` 地址空间，需核对实际分配地址、路由表及策略路由；不能仅靠接口名不同判断无冲突。
- EasyTier 网段不能与 LAN `10.1.1.0/24`、远端 LAN、其他 overlay 重叠。该插件上游接口掩码默认为 `/8`，不要直接以 `10.x` 地址加默认掩码上线；必须按实际虚拟网段配置。
- 不同时让多个工具接管默认路由 / 出口节点 / 全局 DNS；同一个远端子网只选择明确的转发路径。
- LAN 与 VPN 双向转发按需开启，配合各平台 ACL；不要把管理界面暴露到 WAN。
- OpenClash 需检查组网地址、控制端及直连流量的绕过规则，避免被代理形成回路。
- 并行运行还需观察 CPU、内存与吞吐；支持 ARM64 不等于三种 VPN 并发满速已验证。

参考已核对的项目 README / Makefile：`looong-cat/luci-app-netbird`、`whzhni1/luci-app-tailscale`、`EasyTier/luci-app-easytier`；地址与并行 VPN 风险参考 NetBird How NetBird Works、Tailscale Other VPNs 官方文档。

## 2026-11-14：首次配置检查失败修复

- 直接失败：网络测速源码的 `$(if $(find_package iperf3-ssl),+iperf3-ssl,+iperf3)` 在元数据扫描时落到普通 `iperf3`，与个人配置的 SSL 版选择冲突；现在将依赖明确固定为 `+iperf3-ssl`，不放松配置检查。
- `python3-email` 已不是独立包；当前软件源的 `python3-urllib` 包含 email 模块，保留 urllib 并移除旧依赖名。
- 仅设置 `CONFIG_FEED_video=n` 并不能阻止已安装 feed 定义参与 Kconfig 扫描。现在在 feeds update/install 前过滤 video / PON 源。
- 不再下载未选择的 Nikki、Momo、QModem、qBittorrent 和其他无用源码；OpenClash 内置核心是独立于 Nikki 的 `mihomo-alpha` / `mihomo-meta` 软件包的机制，未在本次改变其渠道。
- 只移除 `package/feeds` 下指向未使用 fwknopd 页面和 Squeezelite 的符号链接，保留 feeds 源码，不改写它们的依赖逻辑。
- 新提交推送后应从 `main` 新建一次 WRT-TEST；对旧运行点 Re-run 会继续使用旧提交。

### 本地验证记录

2026-11-14 使用真实 `VIKINGYFY/immortalwrt` 源码提交 `146dc3d5badc0531072f0d0da7114cd667cc63c2`、实际 feeds 和选定插件源码执行 `make defconfig` 与配置检查，通过 35 项覆盖配置及单机型检查；13 项本地回归测试通过。

此次验证不是 GitHub 托管环境的完整构建，未编译工具链或生成可刷写固件。仍有未选中 GStreamer 插件对 video 源图形库的 3 条缺失依赖警告，当前配置未选择相关包，不影响上述配置检查；不要将它们与已经消除的 Kconfig 循环依赖混淆。

## 2026-11-15：OpenClash 内置核心下载地址错误

QCA-ALL #1 的串行编译日志显示下载 `clash-ORE_ARCH.tar.gz` 返回 404。原因是 OpenClash 的 `Build/Compile` 宏中的 `$$CORE_ARCH` 在 OpenWrt 的 `eval` 和 recipe 两次展开中丢失 `$C`，不是目标设备不支持 ARM64，也不是核心文件正常地址返回 404。

`Scripts/customize-vpn-packages.py` 现在仅将该编译块内两处引用改为 `$$$$CORE_ARCH`，保留架构映射、下载来源、内置选项和核心渠道。运行时 shell 才把它展开成 `linux-arm64`。修补具备幂等性，并在上游结构改变时明确失败而非盲目替换。

新增回归测试复现错误地址，并验证修复后的 ARM64 / x86_64 URL、未知架构拒绝，以及 `tee` 不会掩盖编译失败。正式 CI 仍先并行编译，失败后串行 `V=s` 重试，两次完整输出分别存放在：

- `build-reports/compile-parallel.log`
- `build-reports/compile-serial.log`（仅发生重试时存在）

这些文件通过现有 `Upload Build Reports` 步骤上传，即使编译失败也会尝试保留。此改动不补回旧运行的完整日志。

### 如何提供日志

- 公开页面通常可读取状态和步骤结论；完整 Actions 日志 / Artifact 下载可能要求 GitHub 登录。Git SSH 推送凭据并不自动提供 Actions API 读取授权。
- 已登录 GitHub 时，在失败步骤使用 View raw logs / Download log archive（名称可能随界面变化），保存为 `.txt` 或 `.zip` 再上传给助手，无须粘贴数千行。
- 修复后的新运行也可在运行页底部 Artifacts 下载 `build-reports-*`，提供其中的 `compile-serial.log`。
- 不要发送 GitHub 密码或访问令牌。日志分享前检查有无自定义密钥 / 私有下载地址。

本地验证：21 项回归测试通过；使用实际 OpenClash Makefile 的编译块复现原来的 `ORE_ARCH` 地址，并在修复后成功执行 ARM64 核心的下载、解压、安装，校验产物为可执行 AArch64 ELF。没有执行该 ARM64 程序，也没有在本地重编译整套固件。
