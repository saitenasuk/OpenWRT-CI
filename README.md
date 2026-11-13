# 亚瑟 RE-SS-01 个人构建

本 fork 当前只构建京东云亚瑟 `jdcloud_re-ss-01` 的 `IPQ60XX-WIFI-NO` 固件。

- 源码保持 `VIKINGYFY/immortalwrt` 的 `owrt` 分支；NetBird / whzhni1 Tailscale 的 LuCI 源码已固定到检查过的提交，主源码、feeds 和其他插件尚未统一锁定，仍不是官方稳定发行版。
- `QCA-ALL` 仅手动触发，只使用 `IPQ60XX-WIFI-NO`；该配置仅选择亚瑟，保留原有无 Wi-Fi 驱动配置。
- `WRT-TEST` 的平台选择同样收窄为 `IPQ60XX-WIFI-NO`，默认 `TEST=true` 只输出配置。源码选项暂保留上游设置；换源码需另行核对分支、设备及定制脚本兼容性。
- 其他平台入口与 `Auto-Clean` 移至 `.github/workflows-disabled/`；不再每日构建或自动删除固件 Release。`Cache-Clean` 仅清理 Actions 缓存，保持原样。
- 默认 LAN / 管理地址为 `10.1.1.1`，两个手动构建入口保持一致；这是新固件的默认值，保留旧配置升级时不保证覆盖原地址。
- 插件选择集中在 `Config/PRIVATE.txt`：移除 HomeProxy、Gecoos AC、Samba4；添加 OpenClash、EasyTier、网络测速、NetBird、whzhni1 Tailscale。清单见 `docs/PLUGIN-INVENTORY.md`。
- OpenClash 请求内置 Mihomo 核心，EasyTier / NetBird 随包构建核心；Tailscale 使用插件自己的核心下载器，不并装 feeds 的 Tailscale 服务包。VPN / OpenClash 默认关闭，NetBird / Tailscale 默认不接管 DNS、不接受远端子网路由，也不自动开放 LAN 转发。
- `Scripts/PRIVATE.sh` 引入新源码并执行有检查的兼容修补。CI 在 `make defconfig` 后核对包和机型，缺少所选插件或恢复了排除包就失败，不静默发布残缺固件。

构建与上线检查清单见 `docs/BUILD-CHECKLIST.md`。提交并推送到默认分支后，在 Actions 中手动运行 `WRT-TEST` 检查配置；确认后运行 `QCA-ALL`（`TEST=false`）编译。配置检查不等于编译通过，编译通过也不等于真机运行验证。

---

# 高质量<免费>交流群

[IPQ技术讨论群](https://qm.qq.com/q/v7nMhzB4oU)

# 高质量<付费>中转站

[Krill-Code](https://www.krill-code.com/register?invite=959NHQCZGT)

# 本地编译器

https://github.com/VIKINGYFY/OWRT-Tools.git

# 自用修改版插件

https://github.com/VIKINGYFY/packages.git

# OpenWRT-CI

官方版：

https://github.com/immortalwrt/immortalwrt.git

自用版：

https://github.com/VIKINGYFY/immortalwrt.git

# U-BOOT

高通版-沉心：

https://github.com/chenxin527/uboot-qsdk12.5-build.git

高通版-小猪：

https://github.com/1980490718/u-boot-2016.git

联发科-全新版：

https://github.com/VIKINGYFY/UBOOT-CI/releases

联发科-官方版：

https://drive.wrt.moe/uboot/mediatek

# 固件简要说明

固件每天早上5点自动编译。

固件信息里的时间为编译开始的时间，方便核对上游源码提交时间。

MEDIATEK系列、QUALCOMMAX系列、ROCKCHIP系列、X86系列。

# 目录简要说明

workflows——自定义CI配置

Scripts——自定义脚本

Config——自定义配置

## Star History

<a href="https://www.star-history.com/?repos=vikingyfy%2Fopenwrt-ci&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=vikingyfy/openwrt-ci&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=vikingyfy/openwrt-ci&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=vikingyfy/openwrt-ci&type=date&legend=top-left" />
 </picture>
</a>
