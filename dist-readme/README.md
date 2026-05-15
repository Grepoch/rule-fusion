# Rules

由 [rule-fusion](https://github.com/Grepoch/rule-fusion) 自动生成的规则文件仓库，支持 Mihomo / Sing-box / Shadowrocket。

## 更新

- 规则文件每日自动更新
- 更新时间：北京时间 02:00
- GeoIP/GeoSite 每周日自动更新

## 规则集

### 目录结构

| 目录 | behavior | 格式 | 规则类型 | 性能 | 内存 | 适用 |
|------|----------|------|---------|------|------|------|
| `mihomo/<Cat>/<Cat>-Site.mrs` | domain | mrs | 域名/域名通配符 | 优秀 | 低 | Mihomo 系 |
| `mihomo/<Cat>/<Cat>-Site.txt` | domain | text | 域名/域名通配符 | 良好 | 略低 | Mihomo 系 |
| `mihomo/<Cat>/<Cat>-Site.yaml` | domain | yaml | 域名/域名通配符 | 良好 | 略低 | Mihomo 系 |
| `sing-box/<Cat>/<Cat>-Site.srs` | — | binary | 域名/域名通配符 | 优秀 | 低 | Sing-box |
| `sing-box/<Cat>/<Cat>-Site.json` | — | source | 域名/域名通配符 | 一般 | 一般 | Sing-box |
| `Shadowrocket/<Cat>/<Cat>-Site.list` | — | text | 域名/域名通配符 | 良好 | 略低 | Shadowrocket |

### 规则分类

| 分类 | 说明 | 路由建议 |
|------|------|---------|
| Reject | 广告投放、统计追踪 | REJECT |
| Tracking | 用户行为分析、数据收集 | REJECT |
| AI | ChatGPT、Claude、Gemini、Copilot 等 AI 服务 | 代理 |
| Google | Google 全服务 | 代理 |
| GoogleFCM | Firebase 推送服务 | 代理 |
| Telegram | Telegram 通讯 | 代理 |
| Twitter | X (Twitter) | 代理 |
| YouTube | YouTube | 代理 |
| Netflix | Netflix | 代理 |
| Disney | Disney+ | 代理 |
| HBO | HBO Max | 代理 |
| Spotify | Spotify | 代理 |
| Streaming | 国际流媒体合集 | 代理 |
| Microsoft | 微软服务 | 代理 |
| OneDrive | OneDrive / SharePoint | 代理 |
| Apple | Apple 国际服务 | 代理 |
| GitHub | GitHub | 代理 |
| Speedtest | 测速服务 | 代理 |
| Facebook | Facebook / Meta | 代理 |
| Instagram | Instagram | 代理 |
| Discord | Discord | 代理 |
| Reddit | Reddit | 代理 |
| TikTok | TikTok | 代理 |
| Steam | Steam 国际 | 代理 |
| SteamCN | Steam 国服 | 直连 |
| Games | 游戏平台合集 | 代理 |
| Cloudflare | Cloudflare 服务 | 直连/优选 |
| Bilibili | B站 | 直连 |
| China | 中国网站 | 直连 |
| Direct | 直连域名总表 | 直连 |
| Private | 私有网络 / 局域网 | 直连 |
| Proxy | 需代理域名总表 | 代理 |
| DNS | 公共 DNS 服务 | 直连 |
| Download | 下载服务 | 代理 |
| 12306 | 铁路购票 | 直连 |
| Crypto | 加密货币服务 | 代理 |
| Emby | Emby 媒体服务器 | 代理 |
| PayPal | PayPal | 代理 |
| Pixiv | Pixiv 插画平台 | 代理 |
| Bahamut | 巴哈姆特动画疯 | 代理 |

### 使用示例

#### Mihomo

```yaml
BehaviorDN: &BehaviorDN {type: http, behavior: domain, format: mrs, interval: 86400}

rule-providers:
  Reject: {<<: *BehaviorDN, url: "https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/Reject/Reject-Site.mrs"}
  AI: {<<: *BehaviorDN, url: "https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/AI/AI-Site.mrs"}
  Google: {<<: *BehaviorDN, url: "https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/Google/Google-Site.mrs"}
  Telegram: {<<: *BehaviorDN, url: "https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/Telegram/Telegram-Site.mrs"}
  YouTube: {<<: *BehaviorDN, url: "https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/YouTube/YouTube-Site.mrs"}
  Netflix: {<<: *BehaviorDN, url: "https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/Netflix/Netflix-Site.mrs"}
  Spotify: {<<: *BehaviorDN, url: "https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/Spotify/Spotify-Site.mrs"}
  Streaming: {<<: *BehaviorDN, url: "https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/Streaming/Streaming-Site.mrs"}
  China: {<<: *BehaviorDN, url: "https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/China/China-Site.mrs"}
  Proxy: {<<: *BehaviorDN, url: "https://raw.githubusercontent.com/Grepoch/rules/release/mihomo/Proxy/Proxy-Site.mrs"}

rules:
  - RULE-SET,Reject,REJECT
  - RULE-SET,AI,🤖 AI
  - RULE-SET,Google,🔍 Google
  - RULE-SET,Telegram,📱 Telegram
  - RULE-SET,YouTube,▶️ YouTube
  - RULE-SET,Netflix,🎬 Netflix
  - RULE-SET,Spotify,🎵 Spotify
  - RULE-SET,Streaming,🎞 流媒体
  - RULE-SET,China,🇨🇳 直连
  - RULE-SET,Proxy,🌐 代理
  - MATCH,🐟 兜底
```

#### Sing-box

```json
{
  "route": {
    "rule_set": [
      {"type": "remote", "tag": "reject", "format": "binary", "url": "https://raw.githubusercontent.com/Grepoch/rules/release/sing-box/Reject/Reject-Site.srs"},
      {"type": "remote", "tag": "ai", "format": "binary", "url": "https://raw.githubusercontent.com/Grepoch/rules/release/sing-box/AI/AI-Site.srs"},
      {"type": "remote", "tag": "proxy", "format": "binary", "url": "https://raw.githubusercontent.com/Grepoch/rules/release/sing-box/Proxy/Proxy-Site.srs"}
    ],
    "rules": [
      {"rule_set": ["reject"], "action": "reject"},
      {"rule_set": ["ai", "proxy"], "outbound": "proxy"}
    ]
  }
}
```

## GeoIP / GeoSite

GeoIP 和 GeoSite 数据存放在 `geo` 分支：

```
https://raw.githubusercontent.com/Grepoch/rules/geo/ip/geoip.dat
https://raw.githubusercontent.com/Grepoch/rules/geo/ip/geoip.db
https://raw.githubusercontent.com/Grepoch/rules/geo/ip/Country.mmdb
https://raw.githubusercontent.com/Grepoch/rules/geo/site/geosite.dat
https://raw.githubusercontent.com/Grepoch/rules/geo/site/geosite.db
```

## 数据来源

- [@blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)
- [@Loyalsoldier/geoip](https://github.com/Loyalsoldier/geoip)
- [@Loyalsoldier/domain-list-custom](https://github.com/Loyalsoldier/domain-list-custom)
- [@MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat)
- [@HosheaPDNX/rule-set](https://github.com/HosheaPDNX/rule-set)
- [@LM-Firefly/Rules](https://github.com/LM-Firefly/Rules)
- [@666OS/YYDS](https://github.com/666OS/YYDS)

## 说明

本仓库由 [Grepoch/rule-fusion](https://github.com/Grepoch/rule-fusion) 的 CI 自动生成并推送，不接受手动修改。如需反馈规则问题，请到 [rule-fusion Issues](https://github.com/Grepoch/rule-fusion/issues) 提交。

## License

GPL-3.0 — 规则数据著作权归各上游作者所有。
