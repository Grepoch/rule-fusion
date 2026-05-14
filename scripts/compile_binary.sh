#!/usr/bin/env bash
# ============================================================
# compile_binary.sh
# ------------------------------------------------------------
# Compile every source ruleset emitted by fetch_and_merge.py
# into kernel-native binaries:
#
#   dist/mihomo/<cat>.txt    →  dist/mihomo/<cat>.mrs   (mihomo)
#   dist/sing-box/<cat>.json →  dist/sing-box/<cat>.srs (sing-box)
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

shopt -s nullglob

# ---- mihomo: <cat>.txt → <cat>.mrs ----
if [[ -d "${DIST}/mihomo" ]]; then
  for src in "${DIST}/mihomo/"*.txt; do
    out="${src%.txt}.mrs"
    log "mihomo convert-ruleset domain text → ${out#"${ROOT}/"}"
    "${MIHOMO_BIN}" convert-ruleset domain text "${src}" "${out}"
  done
fi

# ---- sing-box: <cat>.json → <cat>.srs ----
if [[ -d "${DIST}/sing-box" ]]; then
  for src in "${DIST}/sing-box/"*.json; do
    out="${src%.json}.srs"
    log "sing-box rule-set compile → ${out#"${ROOT}/"}"
    "${SING_BOX_BIN}" rule-set compile --output "${out}" "${src}"
  done
fi

log "done."
