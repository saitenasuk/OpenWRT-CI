# 停用的上游工作流

这里保留未经修改的上游工作流，方便日后恢复；它们不位于 `.github/workflows/`，不会作为当前仓库的 Actions 工作流加载。

- `AIROHA-ALL.yml`、`MTK-ALL.yml`、`OWRT-ALL.yml`、`QCB-ALL.yml`：其他平台构建，当前只需要亚瑟。
- `Auto-Clean.yml`：原有每日自动清理入口，会删除 Releases、标签及工作流记录；停用以保留已验证固件和回退记录。

不要在未检查触发条件和清理策略前直接移回。同步上游时，也需要检查这些文件是否被重新引入 `.github/workflows/`。
