# 规则分类规划

> 基于仓库 A（HosheaPDNX/rule-set）和仓库 B（666OS/rules）的对比分析，
> 规划 rule-fusion 的完整分类体系。

---

## 一、两仓库对比总览

### 仓库 A：HosheaPDNX/rule-set（stable 分支）

**特点**：
- 按内核分顶级目录：`mihomo/` `sing-box/` `Shadowrocket/`
- 每个分类一个子文件夹，内含多种格式文件
- mihomo 提供：`*-Site.mrs` + `*-Site.yaml` + `*-Site-Classical.yaml` + `*-IP.mrs` + `*-IP.yaml`
- sing-box 提供：V1/V2/V3 三个版本的 `.json` + `.srs`
- 分类较少（20 个），但每个分类格式最全

**分类列表**（20 个）：
12306, AD, AI, Apple, Bahamut, Bilibili, China, DNS, Discord, GFWList, Games, Google, GoogleFCM, Local, Messages, Microsoft, Netflix, OpenAI, Pixiv, Speedtest, Spotify, Steam, SteamCN, Telegram, TikTok

---

### 仓库 B：666OS/rules（release 分支）

**特点**：
- 按内核分顶级目录：`mihomo/` `singbox/` `surge/`
- mihomo 下再分 `domain/` 和 `ip/` 子目录
- 分类丰富（39 个），覆盖面广
- 有 classical 格式（mihomo 根目录的 .txt）+ domain 格式（mihomo/domain/）+ ip 格式（mihomo/ip/）

**分类列表**（39 个）：
AI, Advertising, Apple, AppleCN, Bybit, China, Claude, Cloudflare, Crypto, Direct, Disney, Download, Emby, Facebook, Games, Gemini, GitHub, Google, HBO, Instagram, LocationDKS, Microsoft, Netflix, NewsMedia, OneDrive, OpenAI, PayPal, Private, Proxy, SocialMedia, Speedtest, Spotify, Streaming, SystemOTA, Telegram, TikTok, Tracking, Twitter, XPTV, YouTube

---

## 二、共有分类（14 个）

两个仓库都有的分类，是最核心、最通用的：

| 分类 | A 的命名 | B 的命名 | 说明 |
|------|---------|---------|------|
| 广告拦截 | AD | Advertising | 广告域名 + IP |
| AI 服务 | AI + OpenAI | AI + OpenAI + Claude + Gemini | B 拆得更细 |
| Apple | Apple | Apple + AppleCN | B 区分了国内/国际 |
| 中国直连 | China | China + Direct | B 多了一个 Direct |
| 游戏 | Games | Games | 游戏平台 |
| Google | Google | Google | Google 全服务 |
| Microsoft | Microsoft | Microsoft | 微软服务 |
| Netflix | Netflix | Netflix | Netflix |
| 测速 | Speedtest | Speedtest | Speedtest |
| Spotify | Spotify | Spotify | Spotify |
| Telegram | Telegram | Telegram | Telegram |
| TikTok | TikTok | TikTok | TikTok |
| Steam | Steam | (在 Games 里) | A 单独拆出 |
| Discord | Discord | (在 SocialMedia 里) | A 单独拆出 |

---

## 三、仓库 A 独有分类（B 没有的）

| 分类 | 说明 | 是否建议纳入 rule-fusion |
|------|------|------------------------|
| **12306** | 中国铁路购票 | ✅ 建议纳入（国内直连，防止走代理导致封号） |
| **Bahamut** | 巴哈姆特动画疯（台湾流媒体） | ⚠️ 可选（台湾用户需要） |
| **Bilibili** | B站 | ✅ 建议纳入（国内直连） |
| **DNS** | 公共 DNS 服务 IP | ✅ 建议纳入（防止 DNS 泄漏） |
| **GFWList** | 被墙域名总表 | ⚠️ 可选（太大，且与 Proxy 重叠） |
| **GoogleFCM** | Google Firebase 推送 | ✅ 建议纳入（保证推送不断） |
| **Local** | 局域网 / 私有地址 | ✅ 建议纳入（基础设施） |
| **Messages** | iMessage / FaceTime | ⚠️ 可选（Apple 用户需要） |
| **Pixiv** | 日本插画平台 | ⚠️ 可选 |
| **SteamCN** | Steam 国服 | ✅ 建议纳入（国内直连） |

---

## 四、仓库 B 独有分类（A 没有的）

| 分类 | 说明 | 是否建议纳入 rule-fusion |
|------|------|------------------------|
| **AppleCN** | Apple 国内 CDN / iCloud 中国区 | ✅ 建议纳入（直连优化） |
| **Bybit** | 加密货币交易所 | ⚠️ 可选（Crypto 已覆盖） |
| **Claude** | Anthropic Claude（独立分类） | ✅ 已在 AI 合集中 |
| **Cloudflare** | Cloudflare 服务 | ✅ 建议纳入（直连/优选） |
| **Crypto** | 加密货币全集 | ⚠️ 可选 |
| **Direct** | 国内直连域名总表 | ✅ 建议纳入 |
| **Disney** | Disney+ | ✅ 建议纳入（流媒体） |
| **Download** | 下载服务 | ✅ 建议纳入 |
| **Emby** | Emby 媒体服务器 | ⚠️ 可选 |
| **Facebook** | Facebook / Meta | ✅ 建议纳入 |
| **Gemini** | Google Gemini（独立分类） | ✅ 已在 AI 合集中 |
| **GitHub** | GitHub | ✅ 建议纳入 |
| **HBO** | HBO Max | ⚠️ 可选（流媒体） |
| **Instagram** | Instagram | ✅ 建议纳入 |
| **LocationDKS** | 定位服务解锁 | ⚠️ 可选（特殊用途） |
| **NewsMedia** | 国际新闻媒体 | ⚠️ 可选 |
| **OneDrive** | OneDrive / SharePoint | ✅ 建议纳入 |
| **PayPal** | PayPal | ⚠️ 可选 |
| **Private** | 私有网络 / 内网 | ✅ 建议纳入（同 A 的 Local） |
| **Proxy** | 需要代理的域名总表 | ✅ 建议纳入 |
| **SocialMedia** | 社交媒体合集 | ✅ 建议纳入 |
| **Streaming** | 流媒体合集 | ✅ 建议纳入 |
| **SystemOTA** | 系统升级服务 | ⚠️ 可选（阻止自动更新） |
| **Tracking** | 用户追踪（区别于广告） | ✅ 建议纳入 |
| **Twitter** | X (Twitter) | ✅ 建议纳入 |
| **XPTV** | VOD 资源 | ⚠️ 可选 |
| **YouTube** | YouTube | ✅ 建议纳入 |

---

## 五、rule-fusion 建议的完整分类体系

综合两个仓库，按优先级分层：

### 第一优先级（核心，立即实现）

| 分类 | category 值 | 用途 | 路由策略 |
|------|------------|------|---------|
| Reject | `reject` | 广告 + 追踪拦截 | REJECT |
| AI | `ai` | AI 服务合集 | 代理 |
| Google | `google` | Google 全服务 | 代理 |
| Telegram | `telegram` | Telegram | 代理 |
| Twitter | `twitter` | X (Twitter) | 代理 |
| YouTube | `youtube` | YouTube | 代理 |
| Netflix | `netflix` | Netflix | 代理 |
| Spotify | `spotify` | Spotify | 代理 |
| Microsoft | `microsoft` | 微软服务 | 代理 |
| Apple | `apple` | Apple 国际服务 | 代理 |
| GitHub | `github` | GitHub | 代理 |
| Speedtest | `speedtest` | 测速 | 代理 |

### 第二优先级（常用，近期实现）

| 分类 | category 值 | 用途 | 路由策略 |
|------|------------|------|---------|
| Facebook | `facebook` | Facebook / Meta | 代理 |
| Instagram | `instagram` | Instagram | 代理 |
| Discord | `discord` | Discord | 代理 |
| Reddit | `reddit` | Reddit | 代理 |
| TikTok | `tiktok` | TikTok | 代理 |
| Steam | `steam` | Steam 国际 | 代理 |
| SocialMedia | `socialmedia` | 社交媒体合集 | 代理 |
| Streaming | `streaming` | 流媒体合集 | 代理 |
| Games | `games` | 游戏平台合集 | 代理 |

### 第三优先级（进阶，后期实现）

| 分类 | category 值 | 用途 | 路由策略 |
|------|------------|------|---------|
| China | `china` | 中国直连域名 | 直连 |
| Direct | `direct` | 直连域名总表 | 直连 |
| Private | `private` | 私有网络 / 局域网 | 直连 |
| Proxy | `proxy` | 需代理域名总表 | 代理 |
| Cloudflare | `cloudflare` | Cloudflare | 直连/优选 |
| AppleCN | `applecn` | Apple 国内服务 | 直连 |
| Bilibili | `bilibili` | B站 | 直连 |
| OneDrive | `onedrive` | OneDrive | 代理 |
| Download | `download` | 下载服务 | 代理 |
| Tracking | `tracking` | 用户追踪 | REJECT |
| DNS | `dns` | 公共 DNS | 直连 |

### 可选（特殊需求）

| 分类 | 说明 |
|------|------|
| 12306 | 铁路购票直连 |
| SteamCN | Steam 国服直连 |
| GoogleFCM | Firebase 推送 |
| Bahamut | 巴哈姆特（台湾） |
| Disney / HBO | 流媒体单独拆分 |
| Crypto / Bybit / PayPal | 金融服务 |
| Emby / XPTV | 媒体服务器 |
| NewsMedia | 国际新闻 |
| SystemOTA | 系统升级阻止 |
| Pixiv | 日本插画 |
| LocationDKS | 定位解锁 |

---

## 六、目标产物结构

```
Grepoch/rules@release
├── mihomo/
│   ├── domain/                    # behavior: domain, format: mrs/txt
│   │   ├── Reject.mrs / .txt
│   │   ├── AI.mrs / .txt
│   │   ├── Google.mrs / .txt
│   │   ├── Telegram.mrs / .txt
│   │   ├── ...（每个分类）
│   │   └── Proxy.mrs / .txt
│   ├── ip/                        # behavior: ipcidr, format: mrs/txt（后期）
│   │   ├── Telegram.mrs / .txt
│   │   ├── China.mrs / .txt
│   │   └── ...
│   └── classical/                 # behavior: classical, format: text（后期）
│       ├── AI.txt
│       └── ...
│
├── sing-box/
│   ├── domain/                    # domain_suffix 规则
│   │   ├── Reject.srs / .json
│   │   ├── AI.srs / .json
│   │   └── ...
│   └── ip/                        # ip_cidr 规则（后期）
│       ├── Telegram.srs / .json
│       └── ...
│
├── shadowrocket/
│   ├── Reject.list
│   ├── AI.list
│   └── ...
│
└── surge/                         # 后期可选
    ├── Reject.txt
    └── ...
```

---

## 七、文件格式对照

| 格式 | 仓库 A 命名 | 仓库 B 命名 | rule-fusion 命名 |
|------|------------|------------|-----------------|
| mihomo domain binary | `AI-Site.mrs` | `domain/AI.mrs` | `mihomo/domain/AI.mrs` |
| mihomo domain text | `AI-Site.yaml` | `domain/AI.txt` | `mihomo/domain/AI.txt` |
| mihomo domain yaml | `AI-Site.yaml` | — | `mihomo/domain/AI.yaml` |
| mihomo classical | `AI-Site-Classical.yaml` | `AI.txt`（根目录） | 后期 `mihomo/classical/AI.txt` |
| mihomo ip binary | `AI-IP.mrs` | `ip/AI.mrs` | 后期 `mihomo/ip/AI.mrs` |
| sing-box domain binary | `AI-Site-V2.srs` | `domain/AI.srs` | `sing-box/domain/AI.srs` |
| sing-box domain json | `AI-Site-V2.json` | `domain/AI.json` | `sing-box/domain/AI.json` |
| shadowrocket | `AI-Site.list` | — | `shadowrocket/AI.list` |
| surge | — | `surge/AI.txt` | 后期 `surge/AI.txt` |

---

## 八、与当前 rule-fusion 的差距

| 已实现 | 待实现 |
|--------|--------|
| ✅ Reject (257k 域名) | ❌ IP 规则支持 |
| ✅ AI (105 域名) | ❌ Classical 格式输出 |
| ✅ mihomo/domain/ 结构 | ❌ mihomo/ip/ 结构 |
| ✅ sing-box/domain/ 结构 | ❌ sing-box/ip/ 结构 |
| ✅ shadowrocket/ 结构 | ❌ surge/ 格式 |
| ✅ 多 category 支持 | ❌ 其余 30+ 个 category 的上游源 |
| ✅ Geo 数据 (geo 分支) | ❌ sing-box V1/V2/V3 多版本 |

---

## 九、实施路线

1. **当前**：Reject + AI 已完成
2. **下一步**：在 `upstreams.yaml` 中逐步启用第一优先级的 12 个分类
3. **中期**：加 IP 规则 emitter + classical 格式 emitter
4. **后期**：加 surge 格式 + sing-box 多版本 + 可选分类
