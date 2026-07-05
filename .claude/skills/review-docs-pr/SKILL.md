---
name: review-docs-pr
description: Adversarial fact-check of a Revve docs PR against the product code at origin/prod, followed by fix application and merge. Use when a docs PR needs review before merging, when the user asks to review/verify a documentation PR, or as the review step of an improve-docs round. Takes a PR number or branch name.
---

# Review a Docs PR

One invocation = review one PR → apply the fixes → merge (or report why not). This skill exists because 19 consecutive PR reviews in the 2026-07 docs overhaul found real factual errors in 17 of them — plausible-sounding claims that contradicted prod code — and because unscoped reviews burned 80–180k tokens each when the findings were almost always in the first dozen riskiest claims.

## Phase 1 — Spawn the reviewer (one general-purpose subagent)

The reviewer's brief must include all of the following; deviations are the main source of wasted runs:

**Isolation.** The reviewer must NOT `git checkout` in the primary docs checkout — that invalidates the orchestrator's file state and collides with concurrent work. Instead:
```bash
git fetch origin <branch>
git worktree add --detach /tmp/review-docs-<pr> origin/<branch>   # docs repo, isolated
git -C ../revve-web worktree add --detach /tmp/review-prod-web-<pr> origin/prod   # fact-check source
```
(Add a voice-agent-worker prod worktree only when the PR touches voice-runtime behavior.) The reviewer removes all its worktrees before returning.

**Scope: 10–15 claims, riskiest first.** Order of priority — the partial output of a killed run must still be the valuable part:
1. Safety/permission claims (who can do what, what's reversible, draft-vs-live, "automatically" claims)
2. Verbatim-quoted UI strings and defaults (labels, placeholders, dialog text, numeric defaults/ranges)
3. Behavior claims a user would act on (retry semantics, dedup, what triggers what)
4. Enumerations presented as complete (option lists, status values, node types)
Do NOT ask for exhaustive verification of every sentence. 10–15 deep checks beat 35 shallow ones.

**Standard checks** (cheap, always include): MDX hazards — the linter now catches raw `{{...}}` AND single-brace `{expr}` (renders as empty text), but the reviewer should confirm rendered length is plausible; internal links resolve; docs.json entries exactly once and in the mapped group; no contradictions with the 2–3 most related existing pages; `bash scripts/verify.sh` run from the review worktree.

**Output contract**: findings ranked by severity with file:line and a concrete suggested fix each; a verified-claims list (claim → code evidence); verdict `MERGE_READY` or `FIXES_NEEDED`. Read-only — the reviewer never pushes, edits, comments on GitHub, or merges.

## Phase 2 — Apply fixes (orchestrator, not a new subagent)

- Check out the PR branch in the primary checkout **only now** (after the reviewer is done).
- Apply fixes with `python3` heredoc string replacements rather than the Edit tool when the working tree just changed branches — Edit's read-state goes stale across checkouts and fails repeatedly.
- Distinguish finding classes: factual errors and overclaims must be fixed; "the reviewer would have worded it differently" nits are optional. A finding that reveals a false claim in a *pre-existing* page (outside the PR) gets fixed in the same PR — incorrect docs outrank scope tidiness.
- Re-run `bash scripts/verify.sh` **checking its real exit status** — never pipe it into `tail` inside a `&&` chain (the pipe masks failure; this once shipped a PR with a failing gate).

## Phase 3 — Merge

```bash
git push
sleep 8   # GitHub recomputes mergeability after a push; merging immediately races and fails
gh pr merge <n> --squash --delete-branch || (sleep 15 && gh pr merge <n> --squash --delete-branch)
git checkout main && git pull origin main
```
Merge only with the user's standing authorization for the session/loop; otherwise stop after pushing fixes and report the verdict. Never merge a PR whose verify gate is red or whose MAJOR findings are unaddressed.

## Rails

- A review that terminates early (session limits kill long subagents) is not wasted if it was risk-ordered: apply what it found, then spawn a completion reviewer scoped to ONLY the unchecked remainder — don't re-verify what passed.
- Reviewer findings about the product itself (bugs, PII exposure, dead code) go in the run report to the user, not into the docs.
- Clean up: `git worktree prune` in every repo the review touched.
