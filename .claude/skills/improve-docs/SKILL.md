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

**Docs document production.** Every fact must come from the **`origin/prod`** branch of each product repo — never local `main`/`HEAD`, which carry unmerged dev work and even unpushed local commits (this bit us once: a feature was documented from a local commit that existed nowhere else). Don't type git refs by hand; start with:

```bash
bash scripts/prod_scan.sh begin
```

It fetches `origin/prod` in both repos, computes the unscanned commit range from `.improve-docs-state.json` (first run: last 4 weeks), creates detached **read-only prod worktrees** for code exploration, and prints JSON with the commit lists and worktree paths. Exit 3 means no new prod commits anywhere — Agent A/B have nothing to do; run only Agent C. All code reads happen in the worktrees, never the live checkouts.

Spawn **three Explore subagents in parallel** (single message, three Agent calls):

**Agent A — revve-web recent changes.** Give it the commit list and prod worktree path from `prod_scan.sh begin`, so it never derives git refs itself. Ask it to identify which commits are *customer-facing* (dashboard UI, widget, API routes, integrations, migrations that add user-visible features — not refactors, tests, or internal tooling) and, for each, report: what shipped, exact UI labels/fields/defaults from the code, and which docs page it affects or requires. Tell it the current docs nav (paste the `docs.json` page list).

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

Create a branch first: `improve-docs/<yyyy-mm-dd>-<short-topic>` off **`origin/main`** (`git fetch origin` first) — not local `main`, which may carry unpushed commits that would pollute the PR. If local `main` is ahead of origin, mention that in your final report but don't push it yourself.

Spawn **one writing subagent per page, in parallel**. Each prompt must include:
- The relevant facts from Phase 1 (paste them — the writer should not re-explore the product repos except to verify specifics).
- The full text of `references/writing-standards.md`, or instruct the agent to read it first.
- The target file path, the page's job in one sentence, and which existing pages it links to/from.
- Scope: **write only the assigned page file — never edit `docs.json` or other pages, and never log into the app** (the main agent handles capture in Phase 4). Navigation belongs to the editor pass; parallel writers editing the same nav file will conflict.
- Screenshots: reuse existing images from `/screenshots` where they show current UI; where an image is missing or outdated, write the image reference into the page anyway (`/screenshots/<feature>-<kebab-name>.png` with descriptive alt text) and return the list of needed captures — Phase 4 captures them.

When the writers finish, run the scope guard before touching anything:

```bash
bash scripts/check_writer_scope.sh <assigned-page-1>.mdx <assigned-page-2>.mdx …
```

Any `UNEXPECTED:` path means a writer strayed — revert that file (`git checkout -- <path>`) unless the change was genuinely needed, in which case own it deliberately in the editor pass.

Then do the editor pass yourself: consistent tone across new pages, no duplicated content with existing pages, cross-links in both directions, and add the new pages to the `docs.json` navigation (`navigation.groups`) in a sensible position.

## Phase 4 — Capture screenshots

Collect the writers' needed-capture lists and capture them from the live app. Read `references/screenshot-capture.md` for the full authenticated workflow (magic-link sign-in via Gmail, agent-browser mechanics, naming, and the production-safety rules — they are strict: read-only navigation, release any edit locks, never publish).

For each needed shot: navigate to the screen, put it in the state the page describes, capture at 1440×900 into `/screenshots/`, then **view the image** to confirm it shows what the alt text claims before moving on.

If sign-in or a specific capture fails after a couple of attempts, don't block the run: remove the broken image reference from the page (or keep the old screenshot if it's merely dated, noting it), and list the shot under "Missing screenshots" in the PR body. A shipped PR with two good screenshots beats a stalled run chasing a third.

## Phase 5 — Verify

Run the single gate — it must print `VERIFY PASSED`:

```bash
bash scripts/verify.sh
```

It runs `mint broken-links`, the structural linter (`scripts/check_docs.py`: nav↔file consistency, orphans, missing images, the `{{…}}` page-blanking gotcha, frontmatter, link conventions), and a rendered-body check of every changed page via `mint dev`. Fix errors and re-run until green; warnings don't block but read them — they're usually next-run backlog material (unused screenshots, dimension drift). If a new page intentionally stays out of nav, add it to `scripts/known-orphans.txt` rather than ignoring the error.

## Phase 6 — PR

1. Run `bash scripts/prod_scan.sh finish` — it writes the SHAs Phase 1 actually scanned into `.improve-docs-state.json` (scan-time, not PR-time) and removes the prod worktrees. Include the state file in the commit — it travels with the repo.
2. Commit with a message summarizing the pages added/changed. End with:
   `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
3. Push the branch and open a PR against `main` on **`Revve-AI/docs`** (the repo was transferred from `trungduyvu/docs`; old remotes redirect). Try `gh pr create` first; if it fails auth, fall back to the GitHub MCP `create_pull_request` tool.
4. Finish on a clean tree: `git checkout main` after the PR is open. Never merge the PR yourself.
5. PR body template:

```markdown
## What
- <page>: <one-line why it matters>

## Ranked backlog (next runs)
<remaining top-5 table from Phase 2>

## Missing screenshots (follow-up)
- [ ] <page> — <which screen, what state>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

6. Report the PR URL, what was written, and the top of the remaining backlog.

## Rails

- Never commit to `main` directly; never merge the PR yourself.
- Production safety during screenshot capture (Phase 4 only — writers never log in): navigation and screenshots only. Never publish, save, delete, or send anything; release any edit lock you acquire ("Stop Editing") before leaving a screen; close dialogs with Escape rather than action buttons. Full rules in `references/screenshot-capture.md`.
- Every UI label, default value, field name, and endpoint in a page must come from the product code **at `origin/prod`**, an existing screenshot, or an existing verified page — if you can't ground a claim, leave it out. An outdated claim damages trust more than a missing one, and documenting unshipped features is worst of all.
- Don't delete or rewrite existing non-stub pages in a routine run; propose that in the backlog instead.
- If Phase 1 finds nothing worth writing (all gaps low-score), say so and stop — an empty run is a valid outcome; don't pad a PR.
