---
name: api-reference
description: Documents Revve's public/customer-facing API as a real Mintlify OpenAPI reference — discovers candidate endpoints in ../revve-web/app/api, gates every one behind explicit human approval before it can appear in public docs, authors an OpenAPI spec grounded in the actual route code, wires up the interactive playground, and opens a PR. Use whenever the user asks to document the API, write API reference docs, add an endpoint to the API docs, document webhooks, or invokes /api-reference. improve-docs delegates here for its "API + webhooks reference" backlog item. Pass a focus area (e.g. "threads", "leads", "campaign enrollment") to scope discovery to one resource; pass explicit endpoint paths to skip discovery and go straight to the approval gate for just those.
---

# API Reference

One run = one reviewable PR covering one resource area (e.g. "threads" or "leads + contacts"), never a full-surface dump. The hard rule this skill exists to enforce: **no endpoint reaches public docs without a human explicitly confirming it's meant to be public.** `../revve-web/app/api` is ~95% internal (admin, crons, internal-hooks, webhooks, oauth callbacks); heuristics can and will misfire, so every candidate is a proposal, never a decision.

Before starting, read `references/endpoint-discovery.md` (heuristics + the approval-gate workflow) and `references/openapi-authoring.md` (spec conventions). Create a task list from the phases below.

**Modes** (from the invocation arguments):
- *(no args)* — scan broadly for candidates, subject to the approval gate, ending in a PR.
- A focus area (`threads`, `leads`, `campaign enrollment`, …) — constrain Phase 1's scan to matching routes.
- Explicit endpoint path(s) (e.g. `GET /api/threads/{id}/messages`) — skip Phase 1 discovery, go straight to the Phase 2 approval gate for just those.
- `dry-run` — stop after Phase 2 and report the candidate/approval state. No spec written, no PR.

## Phase 0 — Config prerequisite: mint.json → docs.json

The interactive OpenAPI playground requires the modern `docs.json` config. Check once at the start of every run:

- If `docs.json` already exists and `mint.json` is gone: skip this phase entirely.
- If not: **stop and hand this back to the user as its own task**, don't fold it into a content PR. This is a one-time, site-wide, moderately hard-to-reverse config change (nav schema, colors, topbar CTA all move to a new format) — it deserves its own small PR with hand-verified parity against the live site before `mint.json` is deleted, not a decision made silently mid-run. Report what you found and ask whether to do the migration now as a prerequisite PR, or whether it's already been done since this skill was written.

## Phase 1 — Discover candidate endpoints

Skip this phase entirely if the invocation gave explicit endpoint paths — go straight to Phase 2 with that list.

Otherwise, scan `../revve-web/app/api` (constrained to the focus area if one was given) per the heuristics in `references/endpoint-discovery.md`: auth mechanism (API key/bearer vs. session cookie), path prefix (excluding `/admin`, `/crons`, `/internal-hooks`, `/webhook`, `/oauth`, `/worker`, `/mock`). For each candidate, capture the route path, HTTP methods, file path, and the specific evidence that made it look external-facing.

## Phase 2 — Human confirmation gate

Read `.api-reference-allowlist.json` at the docs repo root (create it with empty `approved`/`rejected` arrays if it doesn't exist). Diff Phase 1's candidates against it:

- Already in `approved` → carries straight to Phase 3.
- Already in `rejected` → drop silently, don't re-surface every run.
- New → present each to the user with its evidence and ask for an explicit yes/no. **Never assume yes.** If this run was delegated non-interactively (e.g. from an automated `improve-docs` pass with no user available to answer), stop here and report the candidate list as the run's output instead of guessing — same as `improve-docs` treating a low-score gap as a valid empty run.

Append decisions to `.api-reference-allowlist.json` as part of this run (approved and rejected both, so rejected candidates don't resurface).

**In dry-run mode: stop here and report the current approved/rejected/pending state.**

## Phase 3 — Author the OpenAPI spec

Spec lives at `api-reference/openapi.json` in this repo — a new file built up incrementally across runs. (Don't reuse or reference `../revve-web/public/openapi.yml`; it's a stale boilerplate example, not real.)

For each allowlisted (approved, not-yet-in-spec) endpoint, derive from the actual route handler in `revve-web` — never guess:
- Path, method, parameters, request body shape, response schema, status codes, from the handler and its validation (zod or equivalent).
- Auth: document the real API-key mechanism (header name/format) as an OpenAPI `securityScheme`, grounded in the same auth check found during discovery.
- Error shape: the handler's actual error response, not a generic assumption.

If a shape can't be verified from code, omit that field rather than guess — outdated/wrong API docs are worse than incomplete ones, same principle as `improve-docs`'s writing-standards.

## Phase 4 — Wire navigation

In `docs.json`, add or extend the `openapi` navigation group pointing at `api-reference/openapi.json`. Set `playground.display: "auth"` (these endpoints require an API key — the interactive playground should only render for authenticated readers). Configure `examples.languages` for cURL, JavaScript, and Python at minimum.

## Phase 5 — Verify

All required before PR:

1. `mint validate` (or whatever spec-lint command the installed `mint` CLI actually exposes — check, don't assume) on `api-reference/openapi.json`. Must pass.
2. `mint broken-links` — must pass.
3. **Allowlist conformance**: every path in the spec must be in `.api-reference-allowlist.json`'s `approved` list. If anything in the spec isn't there, stop and fix it — this is the mechanical backstop behind Phase 2's human gate.
4. Render-check via `mint dev` if available (skip gracefully if the port is busy or the CLI is missing).

## Phase 6 — PR

1. Branch off up-to-date `main`: `api-reference/<yyyy-mm-dd>-<resource-area>`.
2. Commit `.api-reference-allowlist.json` alongside the spec/nav changes — the approval record travels with the repo.
3. Push and open a PR against `main`. Try `gh pr create` first; fall back to the GitHub MCP `create_pull_request` tool if the token is stale.
4. PR body:

```markdown
## What
- Documented: <endpoints newly added to the spec this run>

## Approved this run
- <endpoint> — <one-line evidence>

## Rejected this run
- <endpoint> — <reason, if given>

## Still pending a decision
- <endpoint> — <evidence, awaiting human confirmation>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

5. Report the PR URL and the current allowlist state (counts of approved/rejected/pending).

## Rails

- Never commit to `main` directly; never merge the PR yourself.
- **Never add a path to `api-reference/openapi.json` unless it's in `.api-reference-allowlist.json`'s `approved` list.** This is the one rule the rest of the skill exists to protect.
- Never log into app.revve.ai or read email during a run.
- Every field in the spec must trace to actual route-handler code — no plausible-sounding guesses.
- Don't perform the Phase 0 migration silently as part of a content run — surface it as its own decision.
- If Phase 1/2 yields nothing approved, say so and stop — an empty run is a valid outcome; don't pad a PR with unapproved endpoints to have something to ship.
