# Endpoint Discovery & the Approval Gate

## Why this file exists

`../revve-web/app/api` has ~250 route directories. The large majority are internal: dashboard CRUD called from the app's own frontend with session-cookie auth, `/admin/*`, `/crons/*`, `/internal-hooks/*`, `/webhook/*` (inbound callbacks from third parties like Stripe/Twilio/HubSpot), `/oauth/*` callbacks, `/worker/*`. None of that belongs in public API docs. A route that *looks* like a plausible customer-facing resource (e.g. something under `/threads` or `/leads`) can still be internal-only — heuristics get this wrong. This file is the discovery process; the approval gate in `SKILL.md` Phase 2 is what makes a wrong guess harmless instead of a leaked endpoint.

## Discovery heuristics (Phase 1)

Look for routes where BOTH are true:

1. **Auth mechanism**: the route validates an API key or bearer token — grep for how each route's handler (or a shared middleware it imports) authenticates the caller. Look for patterns like a header check against a stored `team.api_keys`-style value, as opposed to reading a session cookie or NextAuth session. If you can't find where a route authenticates at all, that's a reason for more scrutiny, not a reason to include it.
2. **Path prefix** is not one of the known-internal prefixes: `/admin`, `/crons`, `/internal-hooks`, `/webhook`, `/oauth`, `/worker`, `/mock`. (This list is a starting point, not exhaustive — if you find another prefix that's clearly internal-only by convention, exclude it and note it in the candidate report so the list can be extended over time.)

If a focus area was given (e.g. "threads"), only scan route directories whose path matches it — don't widen the scan just because you're already looking at the code.

## What to capture per candidate

For every candidate, record:
- Route path and HTTP method(s) (e.g. `GET /api/threads/{id}/messages`)
- File path in `revve-web`
- The specific evidence for "external-facing" — quote or point at the actual auth check, not a paraphrase
- Anything that gives you pause (e.g. the handler also accepts a session cookie as an alternate auth path, suggesting it's dual-use) — surface this as a flag, don't silently resolve the ambiguity yourself

A candidate list without evidence is not useful input to Phase 2 — the human confirming needs to see *why* the heuristic flagged it, not just the path.

## The approval gate (Phase 2)

`.api-reference-allowlist.json` at the docs repo root is the durable record:

```json
{
  "approved": [
    { "endpoint": "GET /api/threads", "approvedAt": "2026-07-03", "note": "" }
  ],
  "rejected": [
    { "endpoint": "POST /api/threads/{id}/logs", "rejectedAt": "2026-07-03", "reason": "internal debugging endpoint, not for customers" }
  ]
}
```

Rules:
- A candidate not already in `approved` or `rejected` must be put to the user directly, with its evidence, before any spec-writing happens for it.
- Don't batch-ask ("here are 15 endpoints, approve all?") — go through them so each gets a real yes/no, especially since the whole point is catching the ones that don't belong.
- A `rejected` entry is permanent until someone removes it by hand — don't re-ask about a previously rejected endpoint on a later run.
- If this skill is running non-interactively (delegated from an automated `improve-docs` pass with no one to answer), do not guess. Stop and report the pending list. An automated run that can't get approval produces zero newly-approved endpoints, not a best guess.
