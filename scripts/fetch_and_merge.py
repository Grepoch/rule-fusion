#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_and_merge.py
==================

Pipeline (每个步骤都是纯函数, 便于单测)::

    upstreams.yaml  ┐
    blacklist.txt   ├─► fetch ─► parse ─► dedupe ─► whitelist filter ─► emit
    custom/*.txt    ┘                                                    │
                                                                         ▼
                              dist/{mihomo, sing-box, shadowrocket}/*

输出格式 (针对每个 category, 例如 reject)::

    dist/mihomo/<cat>.txt          mihomo domain-format 文本 (用于编译 .mrs)
    dist/mihomo/<cat>.yaml         mihomo rule-provider 源 (behavior: domain)
    dist/sing-box/<cat>.json       sing-box rule-set 源 (version 2)
    dist/shadowrocket/<cat>.list   shadowrocket / clash-classical 文本

二进制 .mrs / .srs 由 scripts/compile_binary.sh 在 CI 中调用对应内核生成,
本脚本不依赖任何外部内核可执行文件.

CLI::

    python scripts/fetch_and_merge.py            # 拉取 upstreams.yaml 中启用的源
    python scripts/fetch_and_merge.py --offline  # 跳过网络, 仅用 mock + 本地数据
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import requests
import yaml

# --------------------------------------------------------------------------- #
# Paths & constants
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DIST = ROOT / "dist"

UPSTREAMS_FILE = SRC / "upstreams.yaml"
WHITELIST_FILE = SRC / "whitelist.txt"
BLACKLIST_FILE = SRC / "blacklist.txt"
CUSTOM_DIR = SRC / "custom"

HTTP_TIMEOUT = 30
HTTP_RETRY = 3
USER_AGENT = "rule-fusion/1.0 (+https://github.com/Grepoch/rule-fusion)"

# Accepts FQDNs but rejects IPv4 / IPv6 / pure-numeric strings.
# Requires at least one alphabetic character somewhere, which excludes IPs.
DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?=.*[A-Za-z])(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$"
)
# Quick IPv4 / IPv6 detector used as an explicit short-circuit in _normalize.
_IP_RE = re.compile(r"^[0-9.:a-fA-F]+$")

# Built-in mock upstreams. Used by --offline and as fallbacks for `mock://` URLs.
MOCK_UPSTREAMS: dict[str, str] = {
    "mock://virtual-upstream-a": (
        "# Virtual upstream A\n"
        "ads.example.com\n"
        "analytics.example.io\n"
        "example.com\n"          # whitelisted - should be dropped at the end
    ),
    "mock://virtual-upstream-b": (
        "# Virtual upstream B\n"
        "tracker.example.net\n"
        "analytics.example.io\n"  # duplicate with upstream A - should dedupe
        "telemetry.example.dev\n"
    ),
}

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rule-fusion")


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Source:
    name: str
    url: str
    format: str        # domain | classical | hosts | adblock
    category: str      # reject | direct | proxy | ...
    enabled: bool = True


# --------------------------------------------------------------------------- #
# IO helpers
# --------------------------------------------------------------------------- #
def read_lines(path: Path) -> list[str]:
    """Read a text file as stripped, non-empty, non-comment lines."""
    if not path.exists():
        return []
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = strip_inline_comment(raw).strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def strip_inline_comment(line: str) -> str:
    for marker in (" #", " //"):
        if marker in line:
            line = line.split(marker, 1)[0]
    return line


def http_get(url: str) -> str:
    last_err: Exception | None = None
    for attempt in range(1, HTTP_RETRY + 1):
        try:
            log.info("  GET (%s/%s) %s", attempt, HTTP_RETRY, url)
            resp = requests.get(
                url, timeout=HTTP_TIMEOUT, headers={"User-Agent": USER_AGENT}
            )
            resp.raise_for_status()
            return resp.text
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            log.warning("  attempt %s failed: %s", attempt, exc)
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


def fetch_text(url: str, *, offline: bool = False) -> str:
    """Fetch a remote text file. Honors mock:// URLs and --offline."""
    if url.startswith("mock://"):
        if url in MOCK_UPSTREAMS:
            return MOCK_UPSTREAMS[url]
        raise RuntimeError(f"unknown mock URL: {url}")
    if offline:
        log.warning("  --offline: skipping %s", url)
        return ""
    return http_get(url)


# --------------------------------------------------------------------------- #
# upstreams.yaml loader
# --------------------------------------------------------------------------- #
def load_sources() -> list[Source]:
    if not UPSTREAMS_FILE.exists():
        log.warning("upstreams.yaml not found, falling back to built-in mocks")
        return [
            Source(f"mock-{i}", url, "domain", "reject", True)
            for i, url in enumerate(MOCK_UPSTREAMS, 1)
        ]
    data = yaml.safe_load(UPSTREAMS_FILE.read_text(encoding="utf-8")) or {}
    return [
        Source(
            name=item["name"],
            url=item["url"],
            format=item.get("format", "domain"),
            category=item.get("category", "reject"),
            enabled=item.get("enabled", True),
        )
        for item in data.get("sources", [])
    ]


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #
def _normalize(domain: str) -> str:
    """Collapse common prefixes/junk and return a lowercased FQDN, or ''."""
    domain = strip_inline_comment(domain).strip().lower()
    domain = domain.lstrip("|").lstrip("+").lstrip(".").rstrip(".")
    domain = domain.split("^", 1)[0]
    domain = domain.split("/", 1)[0]
    if not domain or _IP_RE.match(domain):
        return ""
    return domain if DOMAIN_RE.match(domain) else ""


def parse_domain(text: str) -> set[str]:
    """Pure domain list, one per line. Tolerates `+.` and `.` prefixes."""
    return {d for d in (_normalize(line) for line in text.splitlines()) if d}


def parse_classical(text: str) -> set[str]:
    """`DOMAIN,foo.com,REJECT` / `DOMAIN-SUFFIX,foo.com` style."""
    out: set[str] = set()
    for raw in text.splitlines():
        line = strip_inline_comment(raw).strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        kind = parts[0].upper()
        if kind in {"DOMAIN", "DOMAIN-SUFFIX", "HOST", "HOST-SUFFIX"}:
            d = _normalize(parts[1])
            if d:
                out.add(d)
    return out


def parse_hosts(text: str) -> set[str]:
    """`0.0.0.0 example.com` / `127.0.0.1 example.com`."""
    out: set[str] = set()
    for raw in text.splitlines():
        line = strip_inline_comment(raw).strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            d = _normalize(parts[1])
            if d:
                out.add(d)
    return out


_ADBLOCK_RE = re.compile(r"^\|\|([A-Za-z0-9.\-]+)\^?")


def parse_adblock(text: str) -> set[str]:
    """Lightweight EasyList parser: `||example.com^`."""
    out: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("!") or line.startswith("#"):
            continue
        m = _ADBLOCK_RE.match(line)
        if m:
            d = _normalize(m.group(1))
            if d:
                out.add(d)
    return out


PARSERS: dict[str, Callable[[str], set[str]]] = {
    "domain": parse_domain,
    "classical": parse_classical,
    "hosts": parse_hosts,
    "adblock": parse_adblock,
}


# --------------------------------------------------------------------------- #
# Pipeline stages
# --------------------------------------------------------------------------- #
def fetch_all(sources: Iterable[Source], *, offline: bool) -> dict[str, set[str]]:
    by_category: dict[str, set[str]] = defaultdict(set)
    for src in sources:
        if not src.enabled:
            log.info("skip disabled: %s", src.name)
            continue
        log.info("fetch: %s [%s → %s]", src.name, src.format, src.category)
        try:
            text = fetch_text(src.url, offline=offline)
        except Exception as exc:  # noqa: BLE001
            log.error("  unreachable, skipped: %s", exc)
            continue
        if not text:
            continue
        parser = PARSERS.get(src.format)
        if not parser:
            log.warning("  unknown format=%s, skipped", src.format)
            continue
        domains = parser(text)
        log.info("  parsed: %d domains", len(domains))
        by_category[src.category].update(domains)
    return by_category


def merge_local(by_category: dict[str, set[str]]) -> None:
    """Merge blacklist.txt + custom/*.{txt,list,yaml,yml} into 'reject'."""
    extra: set[str] = set()

    for line in read_lines(BLACKLIST_FILE):
        d = _normalize(line)
        if d:
            extra.add(d)

    if CUSTOM_DIR.exists():
        for f in sorted(CUSTOM_DIR.iterdir()):
            if f.is_file() and f.suffix.lower() in {".txt", ".list", ".yaml", ".yml"}:
                for line in read_lines(f):
                    d = _normalize(line)
                    if d:
                        extra.add(d)

    if extra:
        log.info("local additions → reject: %d", len(extra))
        by_category.setdefault("reject", set()).update(extra)


def apply_whitelist(by_category: dict[str, set[str]]) -> None:
    """Remove any domain (and its sub-domains) covered by whitelist.txt."""
    wl = {_normalize(line) for line in read_lines(WHITELIST_FILE)}
    wl.discard("")
    if not wl:
        log.warning("whitelist is empty — running without final-defense filter")
        return

    def covered(domain: str) -> bool:
        return any(domain == w or domain.endswith("." + w) for w in wl)

    for cat in list(by_category.keys()):
        before = len(by_category[cat])
        by_category[cat] = {d for d in by_category[cat] if not covered(d)}
        after = len(by_category[cat])
        log.info("whitelist applied to %s: %d → %d (-%d)", cat, before, after, before - after)


# --------------------------------------------------------------------------- #
# Emitters
# --------------------------------------------------------------------------- #
HEADER = "# Generated by rule-fusion. Do not edit manually."


def emit_shadowrocket(domains: list[str], outfile: Path, policy: str = "REJECT") -> None:
    outfile.parent.mkdir(parents=True, exist_ok=True)
    lines = [HEADER, f"# shadowrocket / {outfile.stem}"]
    lines.extend(f"DOMAIN-SUFFIX,{d},{policy}" for d in domains)
    outfile.write_text("\n".join(lines) + "\n", encoding="utf-8")


def emit_mihomo_domain_txt(domains: list[str], outfile: Path) -> None:
    """mihomo domain-format text, ready for `mihomo convert-ruleset domain text`.
    NOTE: No comment lines — mihomo's parser rejects them."""
    outfile.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"+.{d}" for d in domains]
    outfile.write_text("\n".join(lines) + "\n", encoding="utf-8")


def emit_mihomo_yaml(domains: list[str], outfile: Path) -> None:
    """mihomo rule-provider source (behavior: domain, format: yaml)."""
    outfile.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        HEADER,
        "# mihomo rule-provider behavior: domain, format: yaml",
        "payload:",
    ]
    lines.extend(f"  - '+.{d}'" for d in domains)
    outfile.write_text("\n".join(lines) + "\n", encoding="utf-8")


def emit_singbox_source(domains: list[str], outfile: Path) -> None:
    """sing-box rule-set source (version 2), to be compiled to .srs."""
    outfile.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 2,
        "rules": [{"domain_suffix": domains}],
    }
    outfile.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def emit_all(by_category: dict[str, set[str]]) -> None:
    """
    Emit multi-format products into the target directory structure:

        dist/mihomo/domain/<Cat>.txt       (domain-text, for compiling to .mrs)
        dist/mihomo/domain/<Cat>.yaml      (rule-provider yaml source)
        dist/sing-box/domain/<Cat>.json    (rule-set source, for compiling to .srs)
        dist/shadowrocket/<Cat>.list       (text rules)

    Category names are capitalized for consistency with HosheaPDNX/rule-set style:
        reject → Reject, ai → AI, google → Google, etc.
    """
    DIST.mkdir(parents=True, exist_ok=True)

    # Mapping for display-friendly category names
    DISPLAY_NAMES: dict[str, str] = {
        "reject": "Reject",
        "ai": "AI",
        "google": "Google",
        "telegram": "Telegram",
        "socialmedia": "SocialMedia",
        "streaming": "Streaming",
        "microsoft": "Microsoft",
        "apple": "Apple",
        "github": "GitHub",
        "steam": "Steam",
        "tiktok": "TikTok",
        "spotify": "Spotify",
        "netflix": "Netflix",
        "youtube": "YouTube",
        "twitter": "Twitter",
        "facebook": "Facebook",
        "discord": "Discord",
        "reddit": "Reddit",
        "direct": "Direct",
        "proxy": "Proxy",
        "china": "China",
        "download": "Download",
        "speedtest": "Speedtest",
        "games": "Games",
        "crypto": "Crypto",
    }

    for category, domain_set in by_category.items():
        domains = sorted(domain_set)
        if not domains:
            log.info("category=%s is empty, skipping emit", category)
            continue

        # Use display name if mapped, otherwise capitalize first letter
        display = DISPLAY_NAMES.get(category.lower(), category.capitalize())
        log.info("emit category=%s (%s) domains=%d", category, display, len(domains))

        # mihomo/domain/<Cat>.txt  (for binary compilation)
        emit_mihomo_domain_txt(domains, DIST / "mihomo" / "domain" / f"{display}.txt")
        # mihomo/domain/<Cat>.yaml (rule-provider source)
        emit_mihomo_yaml(domains, DIST / "mihomo" / "domain" / f"{display}.yaml")
        # sing-box/domain/<Cat>.json (rule-set source)
        emit_singbox_source(domains, DIST / "sing-box" / "domain" / f"{display}.json")
        # shadowrocket/<Cat>.list
        policy = "REJECT" if category.lower() == "reject" else "PROXY"
        emit_shadowrocket(domains, DIST / "shadowrocket" / f"{display}.list", policy=policy)


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate rule-fusion artifacts.")
    p.add_argument(
        "--offline",
        action="store_true",
        help="Skip remote fetches; only use mock:// upstreams and local data.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    log.info("rule-fusion :: fetch_and_merge")
    log.info("root = %s", ROOT)

    sources = load_sources()
    log.info("loaded %d source(s) from upstreams.yaml", len(sources))

    by_category = fetch_all(sources, offline=args.offline)
    merge_local(by_category)
    apply_whitelist(by_category)
    emit_all(by_category)

    total = sum(len(v) for v in by_category.values())
    log.info("done. total domains across categories = %d", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
