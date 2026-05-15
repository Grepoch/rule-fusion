#!/usr/bin/env bash
# ============================================================
# compile_binary.sh
# ------------------------------------------------------------
# Recursively compile source rulesets into kernel-native binaries:
#
#   dist/mihomo/domain/<Cat>.txt   →  dist/mihomo/domain/<Cat>.mrs
#   dist/mihomo/ip/<Cat>.txt       →  dist/mihomo/ip/<Cat>.mrs
#   dist/sing-box/domain/<Cat>.json → dist/sing-box/domain/<Cat>.srs
#   dist/sing-box/ip/<Cat>.json    →  dist/sing-box/ip/<Cat>.srs
#
# Required env vars (provided by 2-build-release.yml):
#   MIHOMO_BIN    absolute path to the mihomo executable
#   SING_BOX_BIN  absolute path to the sing-box executable
#
# Local usage:
#   MIHOMO_BIN=/path/mihomo SING_BOX_BIN=/path/sing-box bash scripts/compile_binary.sh
# ============================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="${ROOT}/dist"

MIHOMO_BIN="${MIHOMO_BIN:-${ROOT}/bin/mihomo}"
SING_BOX_BIN="${SING_BOX_BIN:-${ROOT}/bin/sing-box}"

log()  { printf '\033[36m[compile]\033[0m %s\n' "$*"; }
fail() { printf '\033[31m[compile]\033[0m %s\n' "$*" >&2; exit 1; }

[[ -x "${MIHOMO_BIN}"   ]] || fail "missing executable mihomo: ${MIHOMO_BIN}"
[[ -x "${SING_BOX_BIN}" ]] || fail "missing executable sing-box: ${SING_BOX_BIN}"

log "mihomo:   $("${MIHOMO_BIN}" -v   2>&1 | head -n 1)"
log "sing-box: $("${SING_BOX_BIN}" version 2>&1 | head -n 1)"

count=0

# ---- mihomo: recursively find all .txt → compile to .mrs ----
while IFS= read -r -d '' src; do
  out="${src%.txt}.mrs"
  # Determine behavior from path: ip/ → ipcidr, domain/ → domain
  if [[ "${src}" == *"/ip/"* ]]; then
    behavior="ipcidr"
  else
    behavior="domain"
  fi
  log "mihomo convert-ruleset ${behavior} text → ${out}"
  "${MIHOMO_BIN}" convert-ruleset "${behavior}" text "${src}" "${out}"
  ((count++)) || true
done < <(find "${DIST}/mihomo" -name '*.txt' -print0 2>/dev/null || true)

# ---- sing-box: recursively find all .json → compile to .srs ----
while IFS= read -r -d '' src; do
  out="${src%.json}.srs"
  log "sing-box rule-set compile → ${out}"
  "${SING_BOX_BIN}" rule-set compile --output "${out}" "${src}"
  ((count++)) || true
done < <(find "${DIST}/sing-box" -name '*.json' -print0 2>/dev/null || true)

log "done. compiled ${count} files."
