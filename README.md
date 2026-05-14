# rule-fusion by Grepoch

> 把嘈杂的上游规则熔炼成干净、可审计、可分发的路由工件。
> Aggregate. Verify. Compile. Distribute.

[![Sync Upstream](https://github.com/Grepoch/rule-fusion/actions/workflows/1-sync-upstream.yml/badge.svg)](https://github.com/Grepoch/rule-fusion/actions/workflows/1-sync-upstream.yml)
[![Build & Release](https://github.com/Grepoch/rule-fusion/actions/workflows/2-build-release.yml/badge.svg)](https://github.com/Grepoch/rule-fusion/actions/workflows/2-build-release.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 项目架构

本项目采用**双仓库分离架构**：

| 仓库 | 定位 | 内容 |
|------|------|------|
| [`Grepoch/rule-fusion`](https://github.com/Grepoch/rule-fusion) | 源码仓库 | 脚本、配置、Actions、文档 |
| [`Grepoch/rules`](https://github.com/Grepoch/rules) | 产物仓库 | 编译后的规则文件（用户订阅此仓库） |

**为什么拆分？**
- 脚本出 bug 不会直接污染用户正在订阅的产物
- `rules` 仓库只允许 CI bot 推送，人类无法直接修改产物
- 订阅链接短且稳定，一旦确定永不变更
- Token 权限隔离：即使源码仓库被入侵，攻击者也无法绕过 CI 直接篡改规则

---

## 项目定位

`rule-fusion` 是一个现代化、半自动化的网络代理规则聚合器。它从多个上游开源项目读取规则，进行清洗、去重、白名单兜底，再输出为多个代理生态可直接消费的格式。

支持目标内核与格式：

| 内核 | 源格式 | 二进制格式 |
|------|--------|-----------|
| Mihomo (Clash Meta) | `.yaml`、`.txt` | `.mrs` |
| Sing-box | `.json` | `.srs` |
| Shadowrocket | `.list`、`.txt` | — |

**本项目不创造新规则、不提供节点、不参与流量转发。** 核心价值在于：

- **多源聚合**：统一处理 domain / classical / hosts / adblock 等异构上游格式
- **半自动审计**：上游变化以 PR 形式提交，必须人工 Review 才能合入
- **白名单兜底**：任何上游都无法误伤白名单内的国民级域名（含子域）
- **多格式产物**：同一份清洗后的域名集合一次性输出所有内核所需的格式
- **产物隔离**：编译产物推送到独立的 [`Grepoch/rules`](https://github.com/Grepoch/rules) 仓库

---

## 目录结构

```text
rule-fusion/                         ← 本仓库（源码）
├── .github/
│   └── workflows/
│       ├── 1-sync-upstream.yml      # 定时拉取 → 创建 PR（需人工合并）
│       └── 2-build-release.yml      # 合并后编译 → 推送到 Grepoch/rules
│
├── src/                             # 维护者手动控制的核心数据
│   ├── upstreams.yaml               # 上游源清单（含格式 / 分类 / 开关）
│   ├── whitelist.txt                # 绝对白名单（最后一道防线，覆盖子域）
│   ├── blacklist.txt                # 自定义黑名单
│   └── custom/                      # 维护者手写补充规则
│       └── reject-extra.txt
│
├── scripts/
│   ├── fetch_and_merge.py           # 拉取 → 解析 → 去重 → 白名单 → 多格式输出
│   └── compile_binary.sh            # 调用 mihomo / sing-box 编译二进制
│
├── docs/
│   ├── RULE_FORMATS.md              # 各内核格式与客户端配置示例
│   └── WORKFLOWS.md                 # 半自动同步与发布流程详解
│
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md

rules/                               ← 产物仓库 (Grepoch/rules)
└── release 分支
    ├── mihomo/
    │   ├── reject.txt               # domain-text 源
    │   ├── reject.yaml              # rule-provider yaml 源
    │   └── reject.mrs               # 二进制（推荐）
    ├── sing-box/
    │   ├── reject.json              # rule-set 源
    │   └── reject.srs               # 二进制（推荐）
    └── shadowrocket/
        └── reject.list              # 文本规则
```

---

## 快速开始

### 本地预览（离线模式，无需联网）

```bash
pip install -r requirements.txt
python scripts/fetch_and_merge.py --offline
ls -lhR dist/
```

`--offline` 会跳过远程上游，使用内置 mock 数据，便于在脱机环境验证 pipeline 链路。

### 启用真实上游

1. 编辑 `src/upstreams.yaml`，把 `enabled: false` 改成 `true`
2. 必要时扩充 `src/whitelist.txt`（建议生产前补到 50+ 条）
3. 运行 `python scripts/fetch_and_merge.py`

---

## 订阅地址

> 所有订阅链接指向 [`Grepoch/rules`](https://github.com/Grepoch/rules) 仓库的 `release` 分支。

### Mihomo (Clash Meta)

```yaml
rule-providers:
  rule-fusion-reject:
    type: http
    behavior: domain
    format: mrs
    url: https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/reject.mrs
    path: ./ruleset/rule-fusion-reject.mrs
    interval: 86400

rules:
  - RULE-SET,rule-fusion-reject,REJECT
```

### Sing-box

```json
{
  "type": "remote",
  "tag": "rule-fusion-reject",
  "format": "binary",
  "url": "https://raw.githubusercontent.com/Grepoch/rules/release/sing-box/reject.srs",
  "update_interval": "1d"
}
```

### Shadowrocket

```text
RULE-SET,https://raw.githubusercontent.com/Grepoch/rules/release/shadowrocket/reject.list,REJECT
```

### CDN 加速（jsDelivr）

```text
https://cdn.jsdelivr.net/gh/Grepoch/rules@release/mihomo/reject.mrs
https://cdn.jsdelivr.net/gh/Grepoch/rules@release/sing-box/reject.srs
https://cdn.jsdelivr.net/gh/Grepoch/rules@release/shadowrocket/reject.list
```

更多客户端配置示例见 [docs/RULE_FORMATS.md](docs/RULE_FORMATS.md)。

---

## 工作流概览

```
                    ┌──────────────────────────────┐
   每日定时 / 手动 ─►│ 1-sync-upstream.yml          │
                    │  拉取 upstreams.yaml         │
                    │  解析 / 去重 / 应用白名单    │
                    │  生成 dist/ 源格式           │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ Pull Request: 人工 Review    │
                    │  ✓ 检查 diff                 │
                    │  ✗ 不合理则关闭              │
                    └──────────────┬───────────────┘
                          merge ⤵
                                   ▼
                    ┌──────────────────────────────┐
                    │ 2-build-release.yml          │
                    │  下载 mihomo / sing-box 最新 │
                    │  编译 .mrs / .srs            │
                    │  推送到 Grepoch/rules@release│
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ Grepoch/rules (产物仓库)     │
                    │  用户订阅 / CDN 分发         │
                    └──────────────────────────────┘
```

完整流程见 [docs/WORKFLOWS.md](docs/WORKFLOWS.md)。

---

## 白名单兜底机制

`src/whitelist.txt` 是项目的最后一道防线。无论上游 reject 列表里写了什么，命中白名单的根域名 **及其所有子域** 都会在最终写盘前被强制剔除：

```python
# 简化示意
final_set = merged_set - {d for d in merged_set if covered_by_whitelist(d)}
```

`covered_by_whitelist` 既匹配根域（`apple.com`）也匹配子域（`sub.apple.com`），避免上游误把国民级域名加入黑名单导致大面积断网。

---

## 来源致谢 (Credits)

感谢以下开源项目和维护者长期整理、生成和维护网络路由规则、地理数据、客户端内核及相关生态工具。本项目的工作建立在这些社区成果之上，主要负责规则清洗、去重、白名单保护、格式转换与自动化分发。

- [SagerNet/sing-box](https://github.com/SagerNet/sing-box) — Sing-box 内核与 `.srs` 规则集
- [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo) — Mihomo 内核与 `.mrs` 规则集
- [LM-Firefly/Rules](https://github.com/LM-Firefly/Rules) — 多客户端规则集
- [Loyalsoldier/geoip](https://github.com/Loyalsoldier/geoip) — GeoIP 多格式产物
- [Loyalsoldier/domain-list-custom](https://github.com/Loyalsoldier/domain-list-custom) — 自定义域名列表生成
- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) — iOS 与代理客户端规则
- [HosheaPDNX/rule-set](https://github.com/HosheaPDNX/rule-set) — 规则集整理与分发
- [666OS/YYDS](https://github.com/666OS/YYDS) — 规则集与代理生态

若你是任意上述著作权人/开发者，不希望本项目聚合、引用或展示，请通过 Issue 联系，本项目会优先尊重原作者和原项目的要求。

If you are a copyright holder of any upstream ruleset and would like the aggregation removed, please open an issue.

---

## 法律免责声明 (Disclaimer)

1. 本项目仅用于网络路由策略研究、规则格式互操作性验证与开源规则聚合实验。
2. 本项目 **不提供、不销售、不推荐、不运营** 任何代理节点、订阅、服务器、账号、密钥或网络访问服务。
3. 项目内的所有规则数据均来源于公开开源项目，本项目仅做去重、合并、白名单过滤、格式转换，**不创造新的规则内容**。
4. 规则的最终用途由使用者自行决定。使用者应自行确认所在国家或地区的法律法规、网络管理要求及使用场景的合规性，自行承担一切使用风险。
5. 本项目不鼓励、不支持任何违反所在地法律法规的行为。

---

## License

[MIT](LICENSE) — 仅适用于本仓库的脚本与编排代码。规则数据本身的著作权归各上游作者所有。
