# API Reference Skill — Design

## Problem

The docs repo has no coverage for Revve's public/customer-facing API. `ranking-rubric.md` (owned by the `improve-docs` skill) already lists this as standing backlog item 6: "API + webhooks reference — threads, leads, contacts, campaign enrollment, exports; webhook payloads. Large; propose as several runs." `improve-docs`'s writing workflow (concept/how-to/settings/recipe MDX templates) doesn't fit this job: API reference docs need an OpenAPI spec, a different verification bar (spec validity, not just broken links), and — critically — a way to avoid accidentally publishing internal/admin endpoints as if they were public API.

`../revve-web/app/api` has ~250 route directories. A scan shows the overwhelming majority are internal: dashboard CRUD, `/admin/*`, `/crons/*`, `/internal-hooks/*`, `/webhook/*` (inbound from third parties), `/oauth/*`. Only a minority look like they're meant for external customers to call directly (evidence: `team/[teamId]/secrets` implies API keys exist as a concept). There is no authoritative existing list of "the public API."

There's also a stale example OpenAPI spec at `../revve-web/public/openapi.yml` (title "Founder Chat Swagger", ngrok URL, boilerplate Query/Document schemas) — not real, not to be reused as a starting point.

## Goal

A new skill, `api-reference`, that can be invoked (directly, or delegated to by `improve-docs`) to identify, verify, and document a slice of Revve's public API, producing a real OpenAPI spec plus wired-up Mintlify navigation — without ever publishing an endpoint that wasn't explicitly confirmed as customer-facing.

## Relationship to `improve-docs`

- `improve-docs` keeps owning discovery/ranking of *all* doc gaps, including backlog item 6.
- Edit to `improve-docs/SKILL.md` Phase 3: when the selected top-ranked item is the API/webhooks gap, instead of spawning the standard per-page MDX writer subagent, it invokes the `api-reference` skill for that item (passing along whatever endpoint area the ranking pointed at, e.g. "threads" or "campaign enrollment").
- `api-reference` also works standalone: a user can invoke it directly ("document the leads API", `/api-reference threads`) to scope a single run to one resource area without going through `improve-docs`'s ranking pass.
- Edit to `ranking-rubric.md` backlog item 6: add a pointer to the new skill so future `improve-docs` runs know to delegate rather than write MDX by hand.

## Non-goals

- This skill does not decide product/business policy about what *should* be public. It surfaces candidates by code heuristics and requires a human to confirm each one. It will not guess based on "this seems like a good idea to expose."
- It does not build API-key issuance/management UI docs (that's a separate, already-tracked gap: "Settings — API keys/secrets" in the backlog).
- It does not attempt a full `app/api` inventory in one run — like `improve-docs`, one run stays scoped to what fits in a reviewable PR (roughly one resource area, e.g. "threads" or "leads + contacts").

## Phases

### Phase 0 — Config prerequisite: mint.json → docs.json migration

Mintlify's OpenAPI playground (interactive "try it", auto-generated request/response examples, auth-aware display) requires the modern `docs.json` config; this repo is still on the legacy `mint.json`. Since this is a one-time, repo-wide, somewhat-hard-to-reverse config change unrelated to any specific endpoint, it ships as its own small prerequisite PR, not bundled with the first API-content PR:

1. Run `mint dev` (or the CLI's dedicated migration command) to autogenerate `docs.json` from the existing `mint.json`.
2. Hand-verify parity against the live-rendered site: logo, colors, topbar CTA button, every navigation group and page from `mint.json` present and in the same order in `docs.json`.
3. Only after parity is confirmed, delete `mint.json` in the same PR.
4. This phase is idempotent — once `docs.json` exists and `mint.json` is gone, later `api-reference` runs skip straight to Phase 1.

This phase runs (and its PR merges) before Phase 1 of the first real content run. It is not repeated per-run.

### Phase 1 — Discover candidate endpoints

Scan `../revve-web/app/api` for routes with signals of being externally-facing:

- Auth middleware/helper checks for an API key or bearer token (not a session cookie) — grep for how each route validates the caller.
- Path is not under a known-internal prefix: `/admin`, `/crons`, `/internal-hooks`, `/webhook`, `/oauth`, `/worker`, `/mock`.
- If a focus area was given (from `improve-docs` delegation or direct invocation, e.g. "threads"), constrain the scan to matching route directories.

Output: a candidate list, each with the route path, HTTP methods, the file path, and the specific evidence (which auth check matched, e.g. "validates `Authorization: Bearer` against `team.api_keys` table in `lib/auth/apiKey.ts`").

### Phase 2 — Human confirmation gate (the safety rail)

This is the core protection against the risk of heuristic false positives (an internal/admin route slipping into public docs). Endpoints are never eligible for spec-writing or navigation until a human has explicitly said yes.

- Maintain `.api-reference-allowlist.json` at the docs repo root, structured like the existing `.improve-docs-state.json`:
  ```json
  { "approved": ["GET /api/threads", "POST /api/threads/{id}/messages", "..."] }
  ```
- Diff Phase 1's candidates against the allowlist. Anything already approved proceeds straight to Phase 3.
- Anything new is presented to the user for an explicit per-endpoint yes/no before the run continues (in an interactive session: ask directly; if `improve-docs` delegated this and is running non-interactively, stop and report the candidate list as the phase's output instead of guessing — same "an empty run is a valid outcome" philosophy `improve-docs` already uses for low-score gaps).
- Approved endpoints are appended to the allowlist as part of this run's commit, so repeat runs over the same resource area don't re-ask.
- Rejected candidates are recorded (with a short reason if given) in the allowlist file too, under a `"rejected"` key, so future scans don't resurface them every run.

### Phase 3 — Author the OpenAPI spec

- Spec lives at `api-reference/openapi.json` in this repo — a new, real file, not a reuse of the stale `revve-web/public/openapi.yml` example.
- For each allowlisted endpoint, derive the path/method, parameters, request body, response schema, and status codes from the actual route handler and its validation schema (zod or equivalent) in `revve-web`. Same grounding rule as `writing-standards.md`: every field, type, and example must trace to code — if a shape can't be verified, omit it rather than guess.
- Auth scheme: document the real API-key mechanism (header name, format) as an OpenAPI `securityScheme`, grounded in the same auth-check code found during discovery.
- Error responses: document the actual error shape the handlers return, not a generic assumption.

### Phase 4 — Wire navigation

- Add/extend an `openapi` group in `docs.json` pointing at `api-reference/openapi.json`.
- Set `playground.display: "auth"` — these endpoints require an API key, so the interactive playground should only be live for authenticated readers, matching Mintlify's guidance for keyed APIs.
- Configure `examples.languages` for the snippet set worth showing (cURL, JavaScript, Python at minimum, matching what `improve-docs`'s existing recipe pages already use for code samples).

### Phase 5 — Verify

All required before PR, same "in full or not at all" bar as `improve-docs`:

1. `mint validate` (or equivalent spec-lint) on `api-reference/openapi.json` — must pass.
2. `mint broken-links` — must pass.
3. **Allowlist conformance check**: every path in the spec must appear in `.api-reference-allowlist.json`'s `approved` list. Fail the run if not — this is the mechanical backstop behind the human gate in Phase 2, catching any drift between what was approved and what got written.
4. Render-check via `mint dev` if available (same graceful-skip-if-busy-port behavior as `improve-docs`).

### Phase 6 — PR

Same conventions as `improve-docs`: branch off up-to-date `main` (`api-reference/<yyyy-mm-dd>-<resource-area>`), commit, push, open PR via `gh pr create` (fallback to GitHub MCP), never merge. PR body additionally lists: endpoints newly approved this run, endpoints rejected this run (for visibility), and any candidates still awaiting a decision.

## File layout

```
.claude/skills/api-reference/
  SKILL.md
  references/
    openapi-authoring.md      # spec conventions: schema naming, error shape, auth scheme, pagination — how to derive from revve-web code
    endpoint-discovery.md      # the heuristics from Phase 1, the allowlist file format and Phase 2 workflow

api-reference/
  openapi.json                 # the real spec, built up incrementally across runs

.api-reference-allowlist.json  # repo root, alongside .improve-docs-state.json
```

## Edits to existing files

- `.claude/skills/improve-docs/SKILL.md` Phase 3: add the delegation branch for the API/webhooks gap.
- `.claude/skills/improve-docs/references/ranking-rubric.md` backlog item 6: note that this item routes to the `api-reference` skill instead of the standard writer flow.

## Open questions carried into implementation

- Exact `mint validate` / spec-lint invocation depends on what the installed `mint` CLI (currently 4.2.255) actually exposes — confirm the command during implementation rather than assuming.
- Whether `docs.json`'s auto-migration from `mint.json` preserves the `topbarCtaButton` field 1:1 or needs a manual equivalent in the new schema — verify against Mintlify's current `docs.json` schema during Phase 0 implementation, not assumed here.
