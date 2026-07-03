#!/usr/bin/env bash
# check_writer_scope.sh — after parallel writer subagents finish, verify the
# working tree changed only where expected. Detection layer for the "writer
# edited docs.json / a neighboring page" failure mode.
#
#   check_writer_scope.sh <allowed-path-or-glob>...
#   e.g. check_writer_scope.sh 'voice-agents/call-transfer.mdx' 'guides/*.mdx'
#
# The editor pass runs it again later with docs.json and screenshots/ added
# to the allowed list. Always-ignored: .claude/worktrees, the scan temp file.
#
# Exit: 0 clean, 1 unexpected changes (printed).
set -euo pipefail
DOCS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DOCS_ROOT"

[ $# -ge 1 ] || { echo "usage: check_writer_scope.sh <allowed-glob>..." >&2; exit 1; }

unexpected=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  path="${line:3}"
  path="${path#\"}"; path="${path%\"}"
  case "$path" in
    .claude/worktrees*|.improve-docs-scan-latest.json) continue ;;
  esac
  ok=0
  for glob in "$@"; do
    # shellcheck disable=SC2254
    case "$path" in
      $glob) ok=1; break ;;
    esac
  done
  if [ "$ok" = 0 ]; then
    echo "UNEXPECTED: $path"
    unexpected=1
  fi
done < <(git status --porcelain)

if [ "$unexpected" = 0 ]; then
  echo "OK: working tree changes are within the allowed paths"
fi
exit $unexpected
