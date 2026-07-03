---
name: improve-docs
description: Routine documentation improvement run for the Revve docs repo. Scans the latest commits in the sibling product repos (../revve-web and ../voice-agent-worker) for shipped-but-undocumented changes, audits the docs for standing gaps (stubs, outdated claims, missing sections), stack-ranks everything by impact, then writes the top 2-3 pages via subagents and opens a PR. Use whenever the user asks to improve the docs, find documentation gaps, run a docs sprint, catch the docs up with the product, write missing docs, or invokes /improve-docs. Pass "dry-run" to produce the ranked gap report without writing anything; pass a focus area (e.g. "voice", "campaigns") to constrain the scan.
---

# Improve Docs

One run = one reviewable PR: scan → rank → write the top 2–3 pages → verify → PR. The goal is steady, compounding improvement, not a big-bang rewrite — a small PR that ships beats a large one that stalls in review.

**Modes** (from the invocation arguments):
- *(no args)* — full run ending in a PR.
- `dry-run` — stop after Phase 2 and present the ranked backlog. No files written, no PR.
- A focus area (`voice`, `campaigns`, `widget`, …) — constrain scanning and ranking to that area. Combines with `dry-run`.

Before starting, read `references/writing-standards.md` (page conventions, templates, MDX gotchas) and `references/ranking-rubric.md` (scoring). Create a task list from the phases below.

## Phase 1 — Discover gaps

Read the state file `.improve-docs-state.json` at the docs repo root. It records the last-scanned commit SHA per product repo:

```json
{ "revve-web": "<sha>", "voice-agent-worker": "<sha>" }
```

If it doesn't exist, this is the first run — scan the last 4 weeks of commits instead.

Spawn **three Explore subagents in parallel** (single message, three Agent calls):

**Agent A — revve-web recent changes.** Give it: the SHA range (`git -C ../revve-web log <last-sha>..HEAD --oneline` — run this yourself first and include the commit list in the prompt so the agent doesn't need to re-derive it). Ask it to identify which commits are *customer-facing* (dashboard UI, widget, API routes, integrations, migrations that add user-visible features — not refactors, tests, or internal tooling) and, for each, report: what shipped, exact UI labels/fields/defaults from the code, and which docs page it affects or requires. Tell it the current docs nav (paste the `mint.json` page list).

**Agent B — voice-agent-worker recent changes.** Same brief, for `../voice-agent-worker`. This repo powers the voice-call runtime, so changes here usually affect the Voice Agents docs (settings, behaviors, normalization, telephony).

**Agent C — standing gaps.** Not tied to commits. Give it the docs nav and ask it to audit: pages that are stubs or thin; claims that may have drifted (model lists, UI labels — spot-check 3–4 against the code); sections the docs lack entirely relative to the product surface (check `../revve-web/app/dashboard` for products with zero docs coverage); and dead-end pages ("contact your Revve team"). Seed it with the known backlog in `references/ranking-rubric.md` § Standing backlog so it verifies rather than rediscovers.

## Phase 2 — Stack-rank

Merge the three reports into one gap list. Score each gap with the rubric in `references/ranking-rubric.md` and produce a table sorted by score:

| Rank | Gap | Type (new-feature / outdated / stub / missing-section) | Reach | Severity | Trust | Effort | Score | Proposed page(s) |

Sanity-check the top items yourself before committing to them: open the relevant code or docs page and confirm the gap is real. A wrong "gap" wastes the whole run.

**In dry-run mode: present the table with a short narrative (what you'd write and why) and stop here.**

Select the top items that fit in **2–3 pages total**. Prefer one coherent theme per PR (e.g., two automations pages) over three unrelated pages — easier to review.

**If the top-ranked item is the "API + webhooks reference" gap** (ranking-rubric.md standing backlog item 6): don't run Phase 3 below. Instead, invoke the `api-reference` skill for the relevant resource area (e.g. "threads", "leads") and let it own discovery, the human-approval gate, spec authoring, and its own PR. Report back its result in place of this skill's own Phase 3–5.

## Phase 3 — Write

Create a branch first: `improve-docs/<yyyy-mm-dd>-<short-topic>` off up-to-date `main`.

Spawn **one writing subagent per page, in parallel**. Each prompt must include:
- The relevant facts from Phase 1 (paste them — the writer should not re-explore the product repos except to verify specifics).
- The full text of `references/writing-standards.md`, or instruct the agent to read it first.
- The target file path, the page's job in one sentence, and which existing pages it links to/from.
- The screenshot policy: **reuse existing images from `/screenshots` only; never log into the app.** If a needed screenshot is missing or shows outdated UI, write the page without it and return the list of missing shots.

Writers return their missing-screenshot lists; collect them for the PR body.

After the writers finish, do an editor pass yourself: consistent tone across new pages, no duplicated content with existing pages, cross-links in both directions, and add the new pages to `mint.json` navigation in a sensible position.

## Phase 4 — Verify

All three checks must pass before the PR:

1. `mint broken-links` — must report success.
2. MDX double-brace check — raw `{{…}}` outside backticks silently blanks a page's body:
   `grep -rn '{{' <new files>` and confirm every occurrence is inside backticks or a code fence.
3. Nav ↔ file consistency — every `mint.json` page has an `.mdx` file and no new orphans were created.

If `mint` is available, also render-check each new page (`mint dev`, request the page, confirm non-trivial body length). Skip gracefully if the port is busy or the CLI is missing.

## Phase 5 — PR

1. Update `.improve-docs-state.json` with the current HEAD SHA of both product repos (include it in the commit — the state travels with the repo).
2. Commit with a message summarizing the pages added/changed. End with:
   `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
3. Push the branch and open a PR against `main` on `trungduyvu/docs`. Try `gh pr create` first; if the gh token is stale, fall back to the GitHub MCP `create_pull_request` tool.
4. PR body template:

```markdown
## What
- <page>: <one-line why it matters>

## Ranked backlog (next runs)
<remaining top-5 table from Phase 2>

## Missing screenshots (follow-up)
- [ ] <page> — <which screen, what state>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

5. Report the PR URL, what was written, and the top of the remaining backlog.

## Rails

- Never commit to `main` directly; never merge the PR yourself.
- Never log into app.revve.ai or read email during a routine run.
- Every UI label, default value, field name, and endpoint in a page must come from the product code, an existing screenshot, or an existing verified page — if you can't ground a claim, leave it out. An outdated claim damages trust more than a missing one.
- Don't delete or rewrite existing non-stub pages in a routine run; propose that in the backlog instead.
- If Phase 1 finds nothing worth writing (all gaps low-score), say so and stop — an empty run is a valid outcome; don't pad a PR.
