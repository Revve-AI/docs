#!/usr/bin/env bash
# verify.sh — the single pre-PR gate for the docs repo. Used by the
# improve-docs and api-reference skills ("run scripts/verify.sh; must pass").
#
#   verify.sh                 full-repo checks, render-check pages changed vs origin/main
#   verify.sh --no-render     skip the mint dev render check (fastest)
#
# Runs: mint broken-links → check_docs.py → render_check.sh (changed pages)
#       → check_allowlist.py + spec validation (when the OpenAPI spec changed).
# Exit 0 only if every required check passes. Warnings don't fail the gate
# but are printed.
set -uo pipefail
DOCS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS="$DOCS_ROOT/scripts"
cd "$DOCS_ROOT"

NO_RENDER=0
[ "${1:-}" = "--no-render" ] && NO_RENDER=1

overall=0
section() { printf '\n=== %s ===\n' "$1"; }

section "mint broken-links"
if command -v mint >/dev/null; then
  out=$(mint broken-links 2>&1); rc=$?
  echo "$out" | tail -3
  [ $rc -ne 0 ] && { echo "FAIL: mint broken-links"; overall=1; }
else
  echo "FAIL: mint CLI not installed"; overall=1
fi

section "check_docs.py (structural lint)"
python3 "$SCRIPTS/check_docs.py"; rc=$?
if [ $rc -eq 1 ]; then echo "FAIL: check_docs.py found errors"; overall=1;
elif [ $rc -eq 2 ]; then echo "NOTE: warnings only — not blocking"; fi

# changed pages vs origin/main (best effort if origin/main unknown)
changed_pages=()
if git rev-parse --verify -q origin/main >/dev/null; then
  while IFS= read -r f; do
    case "$f" in
      *.mdx) changed_pages+=("${f%.mdx}") ;;
    esac
  done < <(git diff --name-only --diff-filter=ACMR origin/main...HEAD -- '*.mdx'; git diff --name-only --diff-filter=ACMR -- '*.mdx')
fi

if [ "$NO_RENDER" = 0 ] && [ ${#changed_pages[@]} -gt 0 ]; then
  section "render_check.sh (${#changed_pages[@]} changed page(s))"
  bash "$SCRIPTS/render_check.sh" "${changed_pages[@]}"; rc=$?
  if [ $rc -eq 1 ]; then echo "FAIL: blank/broken rendered page"; overall=1;
  elif [ $rc -eq 2 ]; then echo "NOTE: render check skipped (environment)"; fi
elif [ "$NO_RENDER" = 0 ]; then
  section "render_check.sh"; echo "no changed .mdx pages detected — skipped"
fi

if [ -f "api-reference/openapi.json" ]; then
  section "OpenAPI spec"
  python3 -c "import json;json.load(open('api-reference/openapi.json'))" \
    && echo "openapi.json: valid JSON" \
    || { echo "FAIL: openapi.json is not valid JSON"; overall=1; }
  if command -v mint >/dev/null && mint openapi-check --help >/dev/null 2>&1; then
    mint openapi-check api-reference/openapi.json || { echo "FAIL: mint openapi-check"; overall=1; }
  fi
  python3 "$SCRIPTS/check_allowlist.py" || { echo "FAIL: allowlist conformance"; overall=1; }
fi

section "result"
if [ "$overall" = 0 ]; then echo "VERIFY PASSED"; else echo "VERIFY FAILED"; fi
exit $overall
