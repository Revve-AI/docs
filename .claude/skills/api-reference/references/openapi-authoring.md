# OpenAPI Authoring Conventions

## Spec location and growth model

`api-reference/openapi.json` in this repo, OpenAPI 3.x. It grows incrementally, run over run, as more endpoints clear the approval gate — never regenerated from scratch, never bulk-populated from a full `app/api` scan. Don't touch paths that are already in the spec unless the run's focus area explicitly includes them.

Don't reuse or point at `../revve-web/public/openapi.yml`. It's a stale template (`title: "Founder Chat Swagger"`, an ngrok server URL, placeholder `Query`/`Document` schemas) left over from early scaffolding — not a real description of any current endpoint.

## Grounding rule

Same principle as `writing-standards.md` in the `improve-docs` skill: outdated or wrong docs are worse than missing docs. Every piece of the spec — path, parameter, request/response shape, status code, error format — must trace to the actual route handler and its validation code (zod schema or equivalent) in `revve-web`. If you can't verify a field from code, leave it out rather than infer it from a similar-looking endpoint.

## What to derive, and from where

- **Path + method**: from the route's file location in `app/api/**/route.ts` and the exported HTTP verb handlers.
- **Path/query parameters**: from how the handler reads `params`/`searchParams`, cross-checked against any validation schema.
- **Request body**: from the schema the handler validates the parsed JSON body against (zod `.parse()`/`.safeParse()` or similar). If there's no validation schema, derive conservatively from how the handler reads fields off the body, and flag in the PR description that this endpoint has no runtime validation to ground against — that's useful signal for the reviewer, not something to paper over.
- **Response schema**: from what the handler actually returns on success — the literal shape of the JSON, not an idealized version of it.
- **Status codes**: only the ones the handler actually returns (including error branches), not a generic REST-convention guess.
- **Auth**: document as an OpenAPI `securityScheme` (`type: apiKey` or `http bearer`, matching what discovery found), header name exactly as the code checks it.
- **Errors**: the handler's actual error response shape (e.g. `{ "error": string }` vs `{ "code": ..., "message": ... }`) — check more than one endpoint's error path before assuming they're all the same shape across the API.

## Mintlify-specific wiring

- `docs.json` navigation: the OpenAPI group/tab points at `api-reference/openapi.json` via the `openapi` key (see Mintlify's API playground docs — this is the `docs.json`-only mechanism, not available under the legacy `mint.json`, which is why Phase 0 is a prerequisite).
- `playground.display: "auth"` — these are API-key-gated endpoints, so the interactive "try it" should only be live for readers who are authenticated, not shown open to anyone browsing the docs.
- `examples.languages`: at minimum cURL, JavaScript, Python — matches the code-sample languages already expected in the `improve-docs` recipe pages, for consistency across the site.
- `examples.autogenerate` / `examples.prefill`: leave at Mintlify defaults unless a specific endpoint needs a hand-authored example (e.g. a payload too complex to usefully autogenerate) — prefer letting the spec drive examples over hand-maintaining them, since hand-maintained examples are exactly the kind of claim that silently goes stale.

## Verification

- `mint validate` (confirm the exact subcommand against the installed CLI — don't assume the flag/command name without checking `mint --help` first, since CLI surface changes across versions).
- Cross-check: every path documented in the spec must appear in `.api-reference-allowlist.json`'s `approved` list (see `endpoint-discovery.md`). This is checked mechanically in `SKILL.md` Phase 5 as a backstop to the human approval gate — don't skip it because "the human already said yes earlier in this run."
