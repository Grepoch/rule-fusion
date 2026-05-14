# 工作流详解

`rule-fusion` 采用「自动拉取 + 人工审核 + 合并后构建发布」的半自动维护模型。这样既保留自动化效率，又避免上游投毒、误杀和异常变更直接进入公开分发产物。

```
   ┌────────────────────┐         ┌────────────────────┐         ┌────────────────────┐
   │ 1-sync-upstream.yml│  PR     │   人工 Review      │  merge  │ 2-build-release.yml│
   │  fetch+merge+emit  │ ──────► │   于 GitHub UI     │ ──────► │  compile + publish │
   └────────────────────┘         └────────────────────┘         └────────────────────┘
                                                                          │
                                                                          ▼
                                                              Grepoch/rules@release
                                                                (独立产物仓库, CDN)
```

---

## 1. 半自动同步：`1-sync-upstream.yml`

### 触发

| 条件 | 说明 |
|------|------|
| `schedule` `0 18 * * *` | 每天 02:00 Asia/Shanghai（即 18:00 UTC） |
| `workflow_dispatch` | 在 Actions 页面手动点击 |

### 执行流程

1. Checkout 仓库
2. 安装 Python 3.12 + `requirements.txt`
3. 运行 `python scripts/fetch_and_merge.py`
   - 读取 `src/upstreams.yaml` 中所有 `enabled: true` 的源
   - 按 `format` 字段分别用 `domain / classical / hosts / adblock` 解析器解析
   - 与 `src/blacklist.txt`、`src/custom/*` 合并
   - 应用 `src/whitelist.txt` 兜底过滤（含子域）
   - 输出到 `dist/{mihomo,sing-box,shadowrocket}/`
4. 调用 `peter-evans/create-pull-request@v6` 创建标题为 `Auto Sync Upstream Rules` 的 PR

### 关键设计

**这个工作流永远不会直接 push 到 `main`。**

它只能创建 PR，等待维护者在 GitHub Files Changed 页面审阅后手动合并。

### Review 重点

- ✅ 高价值域名（apple、icloud、weixin、alipay 等）没有被加入 reject
- ✅ 白名单兜底依然生效（看脚本日志中的 `whitelist applied to reject: ... → ... (-N)` 行）
- ✅ 新增 / 删除域名数量在合理区间（突然激增或归零都可能是上游异常）
- ✅ 没有可疑域名混入（拼写相近的钓鱼域名等）

---

## 2. 编译与发布：`2-build-release.yml`

### 触发

| 条件 | 说明 |
|------|------|
| `push` 到 `main` | 当上面的 PR 被合并时即触发 |
| `workflow_dispatch` | 手动触发 |

### 执行流程

1. Checkout 仓库
2. 重新生成 `dist/` 源格式（保证幂等）
3. **从 GitHub Releases API 动态拉取最新版** mihomo 与 sing-box
   - mihomo: `mihomo-linux-amd64-compatible-v*.gz`
   - sing-box: `sing-box-*-linux-amd64.tar.gz`
4. 调用 `scripts/compile_binary.sh`，遍历 dist 中的源文件批量编译
   - `dist/mihomo/*.txt` → `dist/mihomo/*.mrs`
   - `dist/sing-box/*.json` → `dist/sing-box/*.srs`
5. `peaceiris/actions-gh-pages@v4` 通过 deploy key 把整个 `dist/` 推送到 `Grepoch/rules` 仓库的 `release` 分支（`force_orphan`）

### 为什么动态拉取而不是写死版本

写死版本的代价是每次内核升级都要改 workflow；用 GitHub Releases API + `jq` 过滤，CI 永远跟最新稳定版走，零维护。

### 为什么推送到独立仓库

- 脚本 bug 不会直接污染用户正在订阅的产物
- `rules` 仓库只允许 CI bot 推送（deploy key），人类无法直接修改
- 订阅链接更短、语义更清晰
- Token 权限隔离：源码仓库被入侵也无法绕过 CI 篡改规则

### 分发链接结构

产物推送到 `Grepoch/rules` 的 `release` 分支，最终订阅地址：

```text
# Raw GitHub
https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/reject.mrs
https://raw.githubusercontent.com/Grepoch/rules/release/sing-box/reject.srs
https://raw.githubusercontent.com/Grepoch/rules/release/shadowrocket/reject.list

# jsDelivr CDN
https://cdn.jsdelivr.net/gh/Grepoch/rules@release/mihomo/reject.mrs
https://cdn.jsdelivr.net/gh/Grepoch/rules@release/sing-box/reject.srs
https://cdn.jsdelivr.net/gh/Grepoch/rules@release/shadowrocket/reject.list
```

---

## 维护原则

| 原则 | 理由 |
|------|------|
| 不在 `main` 手工修改 `dist/` | 产物由脚本生成，避免漂移 |
| 新增上游必须默认 `enabled: false` | 先在本地跑一遍、对过 diff 再开启 |
| 白名单是最后一道防线 | 任何远程数据都不能覆盖它 |
| 必须经过 PR Diff 审查 | 这是防投毒的核心，不可绕过 |
| 二进制依赖 CI 即时下载 | 不把 mihomo / sing-box 二进制提交进仓库 |

---

## 故障排查

### `peter-evans/create-pull-request` 没有创建 PR

- 检查仓库 Settings → Actions → Workflow permissions 是否启用 "Read and write" 与 "Allow GitHub Actions to create and approve pull requests"
- 检查 `dist/` 是否真的产生了 diff（无变化时不会创建 PR，是预期行为）

### `release` 分支没出现

- 第一次推送时 `peaceiris/actions-gh-pages@v4` 会在 `Grepoch/rules` 仓库创建 `release` 分支；确保 deploy key 有 write 权限
- 确认 `DEPLOY_KEY_RULES` secret 已正确配置（完整私钥，含 BEGIN/END 行）

### mihomo / sing-box 下载失败

- GitHub API 偶发限流，重试一次通常即可
- 内核改了 release asset 命名时需要更新 workflow 中的 `jq` 过滤正则

### 白名单没起效

- 确认 `src/whitelist.txt` 一行一个根域、不带 `+.` 前缀
- 看 sync 工作流日志中 `whitelist applied to reject: ... → ... (-N)` 的 `N`，应大于 0
