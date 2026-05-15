# 项目上下文与设计决策记录

> 本文档记录 `rule-fusion` 项目从零构建到当前状态的完整设计思路、架构决策、踩坑记录。
> 目的是让任何 AI 助手或协作者在阅读本文档后，能完整理解项目并继续开发。

---

## 一、项目定位

`rule-fusion` 是一个**半自动化的网络代理规则聚合器**。

- **不创造规则**：只从上游开源项目拉取、清洗、去重、格式转换
- **不提供节点**：不参与任何流量转发
- **核心价值**：多源聚合 + 人工审计 + 白名单兜底 + 多内核多格式输出

---

## 二、双仓库架构

```
Grepoch/rule-fusion (源码仓库)          Grepoch/rules (产物仓库)
├── src/upstreams.yaml                  ├── release 分支
├── src/whitelist.txt                   │   ├── mihomo/domain/{Reject,AI,...}.{txt,yaml,mrs}
├── src/blacklist.txt                   │   ├── sing-box/domain/{Reject,AI,...}.{json,srs}
├── src/custom/*.txt                    │   └── shadowrocket/{Reject,AI,...}.list
├── scripts/fetch_and_merge.py          │
├── scripts/compile_binary.sh           └── geo 分支
├── .github/workflows/                      ├── ip/{geoip.dat, geoip.db, Country.mmdb}
│   ├── 1-sync-upstream.yml                 └── site/{geosite.dat, geosite.db}
│   ├── 2-build-release.yml
│   └── 3-geo.yml
└── docs/
```

### 为什么拆成两个仓库

| 考量 | 决策 |
|------|------|
| 维护者是 AI 辅助开发者（非专业程序员） | 物理隔离降低误操作风险 |
| 防投毒 | rules 仓库只允许 CI bot（deploy key）推送，人类无法直接改产物 |
| 订阅链接稳定性 | 一旦确定永不变更，避免用户手动改配置 |
| Token 权限隔离 | 源码仓库被入侵也无法绕过 CI 篡改规则 |

### 跨仓库推送机制

- 使用 **deploy key**（ed25519），公钥加到 `Grepoch/rules` 的 Deploy Keys（write access）
- 私钥存为 `Grepoch/rule-fusion` 的 Secret `DEPLOY_KEY_RULES`
- `peaceiris/actions-gh-pages@v4` 的 `external_repository` + `deploy_key` 参数实现跨仓库推送

---

## 三、数据流 Pipeline

```
upstreams.yaml (启用的源)
        │
        ▼
fetch_and_merge.py
  ├── 按 format 字段选择 parser (domain/classical/hosts/adblock)
  ├── 按 category 字段分桶 (reject/ai/google/telegram/...)
  ├── 合并 blacklist.txt + custom/*.txt → reject 桶
  ├── 应用 whitelist.txt 兜底过滤（含子域匹配）
  └── emit 到 dist/ 的目标目录结构
        │
        ▼
compile_binary.sh
  ├── find dist/mihomo -name '*.txt' → mihomo convert-ruleset → .mrs
  └── find dist/sing-box -name '*.json' → sing-box rule-set compile → .srs
        │
        ▼
peaceiris/actions-gh-pages → Grepoch/rules@release
```

---

## 四、关键设计决策

### 4.1 白名单子域感知

```python
def covered(domain):
    return any(domain == w or domain.endswith("." + w) for w in whitelist)
```

白名单里写 `apple.com`，会同时保护 `apple.com` 和 `sub.apple.com`。
**代价**：`mobads.baidu.com`（百度广告）也会被 `baidu.com` 白名单豁免。
**接受理由**：宁可漏拦也不误杀；广告子域由上游 25 万条覆盖。

### 4.2 IP 地址过滤

blackmatrix7 的 `Advertising_Domain.txt` 混入了 IP 地址（如 `103.21.91.144`）。
修复：在 `_normalize()` 中加了 `_IP_RE` 短路检测，纯数字+点+冒号的字符串直接返回空。

### 4.3 mihomo 不接受注释行

`mihomo convert-ruleset domain text` 会在遇到 `#` 开头的行时报错退出。
修复：`emit_mihomo_domain_txt()` 不再输出注释头。

### 4.4 bash `((count++))` 在 set -e 下的陷阱

当 count 从 0 变为 1 时，`((0))` 的退出码是 1，触发 `set -e` 退出。
修复：`((count++)) || true`。

### 4.5 Geo 数据来源

| 文件 | 来源 |
|------|------|
| `geoip.dat` | Loyalsoldier/geoip |
| `Country.mmdb` | Loyalsoldier/geoip |
| `geoip.db` | MetaCubeX/meta-rules-dat |
| `geosite.dat` | Loyalsoldier/domain-list-custom |
| `geosite.db` | MetaCubeX/meta-rules-dat |

Loyalsoldier 只提供 `.dat` 和 `.mmdb`，不提供 `.db`。
`.db` 格式（sing-box/mihomo 用）来自 MetaCubeX。

### 4.6 Category → 文件名映射

`upstreams.yaml` 里的 `category` 字段决定输出文件名：
- `category: reject` → `Reject.mrs`
- `category: ai` → `AI.mrs`
- `category: google` → `Google.mrs`

映射表在 `emit_all()` 的 `DISPLAY_NAMES` 字典中。未映射的 category 会 capitalize 首字母。

### 4.7 动态拉取内核版本

`2-build-release.yml` 用 GitHub Releases API + `jq` 动态获取最新 mihomo/sing-box 二进制，不写死版本号，零维护。

---

## 五、工作流触发逻辑

| Workflow | 触发条件 | 产出 |
|----------|---------|------|
| `1-sync-upstream.yml` | 每天 18:00 UTC / 手动 | PR（需人工合并） |
| `2-build-release.yml` | push 到 main（src/scripts/requirements 变化时） | Grepoch/rules@release |
| `3-geo.yml` | 每周日 19:00 UTC / 手动 | Grepoch/rules@geo |

所有 workflow 都有 `if: github.repository == 'Grepoch/rule-fusion'` 防止 fork 触发。

---

## 六、维护者操作手册

| 操作 | 做什么 |
|------|--------|
| 加上游源 | 编辑 `src/upstreams.yaml`，加一条 `enabled: false`，本地验证后改 true |
| 加白名单 | 编辑 `src/whitelist.txt`，加根域名 |
| 加黑名单 | 编辑 `src/blacklist.txt` 或 `src/custom/*.txt` |
| 本地预览 | `python3 scripts/fetch_and_merge.py && ls dist/` |
| 等自动同步 | 什么都不做，等 PR 出来 Review 后 Merge |
| 手动触发 | Actions 页面 Run workflow |

**永远不需要 clone 或编辑 `Grepoch/rules` 仓库。**

---

## 七、参考项目

| 项目 | 参考了什么 |
|------|-----------|
| [666OS/rules](https://github.com/666OS/rules) | 双分支架构（release + geo）、目录结构 |
| [HosheaPDNX/rule-set](https://github.com/HosheaPDNX/rule-set) | `mihomo/domain/` + `mihomo/ip/` 子目录结构、多分类 |
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) | 主要上游数据源 |
| [Loyalsoldier/geoip](https://github.com/Loyalsoldier/geoip) | GeoIP 数据 |
| [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat) | .db 格式 Geo 数据 |

---

## 八、已知限制与未来计划

### 当前限制

- 只处理域名规则，不处理 IP-CIDR 规则（`mihomo/ip/` 目录预留但未实现）
- 白名单子域保护会豁免大厂的广告子域（设计取舍，由上游覆盖）
- `--offline` 模式只有 mock 数据，无法预览真实上游效果

### 未来可扩展

- 加 IP 规则 emitter（输出到 `mihomo/<Cat>/<Cat>-IP.txt`）
- 加 classical 格式 emitter（`mihomo/<Cat>/<Cat>-Site-Classical.yaml`）
- 加 surge 格式 emitter
- 加 sing-box 多版本支持（V1/V2/V3）
- 补充 AppleCN / Messages / NewsMedia / XPTV / LocationDKS / SystemOTA（需手动整理源）

---

## 九、Commit 历史摘要

```
9e72432 feat: enable all 40 categories (17 recommended + 14 optional)
a6df33f refactor: adopt HosheaPDNX directory structure (mihomo/<Cat>/<Cat>-Site.mrs)
790984d feat: add AI category with 105 domains
e503c40 docs: add CATEGORY_PLAN.md
ded6447 docs: add CONTEXT.md
0825b1a feat: add production blacklist (telemetry, ad SDK, mining, phishing)
afebfa6 docs: update README with maintenance guide
1edfc24 fix: correct geo download URLs (.db from MetaCubeX, not Loyalsoldier)
e91b9da fix: bash compat issues in compile_binary.sh
38a503c fix: remove comment lines from mihomo domain txt
113de06 feat: multi-category + subdirectory structure + geo workflow
20bbf92 refactor: split to dual-repo architecture (rule-fusion + rules)
c03e5af feat: production hardening (whitelist 100+, IP filter fix, CODEOWNERS, fork guard)
a3ac691 Merge PR #1 (first successful auto-sync)
3f343e4 feat: initial scaffold
```

---

## 十、给其他 AI 助手的提示

如果你是另一个 AI 助手被要求继续开发此项目：

1. **先读 `src/upstreams.yaml`** — 了解当前启用了哪些上游（目前 40 个分类）
2. **先读 `scripts/fetch_and_merge.py`** — 这是核心 pipeline，所有逻辑在这里
3. **不要碰 `Grepoch/rules` 仓库** — 它是纯自动化产物，由 CI 管理
4. **改完代码先本地跑 `python3 scripts/fetch_and_merge.py --offline`** — 验证不报错
5. **注意白名单的子域保护** — 加黑名单前检查是否会被白名单豁免
6. **mihomo 的 domain txt 不能有注释行** — 这是一个已踩过的坑
7. **bash 脚本里 `((count++))` 要加 `|| true`** — `set -e` 下的陷阱
8. **deploy key 只对 rules 仓库有写权限** — secret 名为 `DEPLOY_KEY_RULES`
9. **目录结构是 `mihomo/<Cat>/<Cat>-Site.mrs`** — 不是 `mihomo/domain/<Cat>.mrs`
10. **白名单只过滤 reject 和 tracking** — 其他 category 是路由规则，不应被白名单干扰
11. **`dist-readme/README.md` 会被复制到 rules 仓库** — 修改它等于修改 rules 仓库的 README
12. **CONTEXT.md 由 Kiro hook 自动提醒更新** — 每次重大变更后 AI 会被提醒更新此文件
