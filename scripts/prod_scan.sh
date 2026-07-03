#!/usr/bin/env bash
# prod_scan.sh — origin/prod commit-range + state-file manager for the
# improve-docs skill. Makes "scan the wrong git ref" structurally impossible:
# the agent never types a ref, it uses this script's output.
#
#   prod_scan.sh begin    fetch origin/prod in both product repos, compute the
#                         unscanned commit range from .improve-docs-state.json
#                         (fallback: last 4 weeks on first run), create
#                         detached read-only worktrees, print JSON, and save it
#                         to .improve-docs-scan-latest.json (untracked).
#   prod_scan.sh finish   write the scanned SHAs from that file into
#                         .improve-docs-state.json and remove the worktrees.
#
# Exit: 0 ok, 1 repo/fetch failure, 3 (begin) nothing new to scan.
set -euo pipefail

DOCS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_FILE="$DOCS_ROOT/.improve-docs-state.json"
SCAN_FILE="$DOCS_ROOT/.improve-docs-scan-latest.json"
REPOS=("revve-web" "voice-agent-worker")

begin() {
  local entries=() total=0
  for repo in "${REPOS[@]}"; do
    local dir="$DOCS_ROOT/../$repo"
    [ -d "$dir/.git" ] || { echo "ERROR: $dir is not a git repo" >&2; exit 1; }
    git -C "$dir" fetch --quiet origin prod || { echo "ERROR: fetch failed for $repo" >&2; exit 1; }

    local head_sha last_sha range
    head_sha=$(git -C "$dir" rev-parse origin/prod)
    last_sha=$(python3 -c "
import json,sys
try: print(json.load(open('$STATE_FILE')).get('$repo',''))
except FileNotFoundError: print('')" )

    if [ -n "$last_sha" ] && git -C "$dir" cat-file -e "$last_sha" 2>/dev/null; then
      range="$last_sha..origin/prod"
    else
      range="origin/prod --since=4.weeks"
    fi

    local commits
    commits=$(git -C "$dir" log --no-merges --pretty='%h %s' $range 2>/dev/null || true)
    local count
    count=$(printf '%s' "$commits" | grep -c . || true)
    total=$((total + count))

    local worktree=""
    if [ "$count" -gt 0 ]; then
      worktree=$(mktemp -d "${TMPDIR:-/tmp}/${repo}-prod.XXXXXX")
      rmdir "$worktree"
      git -C "$dir" worktree add --quiet --detach "$worktree" origin/prod
    fi

    entries+=("$(SCAN_COMMITS="$commits" python3 - "$repo" "$last_sha" "$head_sha" "$count" "$worktree" <<'PY'
import json, os, sys
repo, last, head, count, worktree = sys.argv[1:6]
commits = [l for l in os.environ.get("SCAN_COMMITS", "").split("\n") if l.strip()]
print(json.dumps({"repo": repo, "last_sha": last or None, "head_sha": head,
                  "commit_count": int(count), "worktree": worktree or None,
                  "commits": [{"sha": c.split(" ", 1)[0],
                               "subject": c.split(" ", 1)[1] if " " in c else ""}
                              for c in commits]}))
PY
)")
  done

  printf '{"repos": [%s]}\n' "$(IFS=,; echo "${entries[*]}")" | python3 -m json.tool | tee "$SCAN_FILE"
  if [ "$total" -eq 0 ]; then
    echo "NOTHING NEW: no unscanned origin/prod commits in any repo" >&2
    exit 3
  fi
}

finish() {
  [ -f "$SCAN_FILE" ] || { echo "ERROR: no $SCAN_FILE — run 'begin' first" >&2; exit 1; }
  python3 - "$SCAN_FILE" "$STATE_FILE" <<'PY'
import json, sys
scan = json.load(open(sys.argv[1]))
try:
    state = json.load(open(sys.argv[2]))
except FileNotFoundError:
    state = {}
for r in scan["repos"]:
    state[r["repo"]] = r["head_sha"]
with open(sys.argv[2], "w") as f:
    json.dump(state, f, indent=2)
    f.write("\n")
print("state updated:", json.dumps(state))
PY
  # remove worktrees
  while read -r repo wt; do
    [ -n "$wt" ] && [ "$wt" != "None" ] && git -C "$DOCS_ROOT/../$repo" worktree remove --force "$wt" 2>/dev/null || true
  done < <(python3 -c "
import json
for r in json.load(open('$SCAN_FILE'))['repos']:
    print(r['repo'], r['worktree'])")
  rm -f "$SCAN_FILE"
  echo "worktrees removed, scan file cleaned up"
}

case "${1:-}" in
  begin) begin ;;
  finish) finish ;;
  *) echo "usage: prod_scan.sh {begin|finish}" >&2; exit 1 ;;
esac
