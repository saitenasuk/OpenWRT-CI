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
缺包、依赖冲突、选项被取消应先修复，不要绕过检查。生成的 `Config-...txt` 需包含 11 个应用、EasyTier / NetBird 核心、TUN / WireGuard 模块，且没有三个已删除应用及专用服务、普通 iperf3 和 feeds 的 Tailscale 包。

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
