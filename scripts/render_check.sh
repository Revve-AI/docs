#!/usr/bin/env bash
# render_check.sh — detect blank-body MDX pages (the raw-{{...}} failure mode
# and any other MDX compile error: the TOC renders but the body is empty).
#
#   render_check.sh <page-id>...      e.g. render_check.sh voice-agents/call-transfer
#
# Starts `mint dev` on a free port, fetches each page, strips tags, and
# requires a minimum amount of rendered body text.
#
# Exit: 0 all pass, 1 any page blank/failed, 2 environment problem
#       (mint missing / server never became ready) — callers may skip
#       gracefully on 2.
set -uo pipefail

DOCS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIN_TEXT_CHARS="${MIN_TEXT_CHARS:-900}"
PORT="${RENDER_CHECK_PORT:-4111}"

[ $# -ge 1 ] || { echo "usage: render_check.sh <page-id>..." >&2; exit 2; }
command -v mint >/dev/null || { echo "SKIP: mint CLI not installed" >&2; exit 2; }

cd "$DOCS_ROOT"
LOG=$(mktemp)
mint dev --port "$PORT" >"$LOG" 2>&1 &
MINT_PID=$!
trap 'kill "$MINT_PID" 2>/dev/null; wait "$MINT_PID" 2>/dev/null; rm -f "$LOG"' EXIT

ready=0
for _ in $(seq 1 60); do
  if curl -sf -o /dev/null "http://localhost:$PORT"; then ready=1; break; fi
  kill -0 "$MINT_PID" 2>/dev/null || break
  sleep 1
done
[ "$ready" = 1 ] || { echo "SKIP: mint dev never became ready (see $LOG)" >&2; exit 2; }

fail=0
for page in "$@"; do
  page="${page#/}"; page="${page%.mdx}"
  html=$(curl -s "http://localhost:$PORT/$page")
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/$page")
  # strip script/style, then all tags, collapse whitespace
  text=$(printf '%s' "$html" | python3 -c "
import re,sys
h=sys.stdin.read()
h=re.sub(r'<(script|style)[^>]*>.*?</\\1>','',h,flags=re.S)
h=re.sub(r'<[^>]+>',' ',h)
print(len(re.sub(r'\\s+',' ',h).strip()))")
  if [ "$code" = "200" ] && [ "$text" -ge "$MIN_TEXT_CHARS" ]; then
    echo "PASS $page (HTTP $code, ${text} chars of rendered text)"
  else
    echo "FAIL $page (HTTP $code, ${text} chars — blank body or render error)"
    fail=1
  fi
done
exit $fail
