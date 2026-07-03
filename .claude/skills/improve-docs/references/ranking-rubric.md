# Gap Ranking Rubric

Score each gap 1–5 on four dimensions, then: **Score = Reach + Severity + Trust − (Effort − 1)**. Sort descending; break ties by lower effort. The numbers are a forcing function for honest comparison, not precision — sanity-check the top of the list against judgment before writing.

## Dimensions

**Reach** — how many users hit this gap, weighted by journey position. Quickstart/onboarding path = 5. Core configuration every builder touches = 4. One channel or one integration = 3. Power-user/edge features = 2. Internal-ish = 1.

**Severity** — what happens to the user at the gap. Task impossible without support contact = 5. Task possible but error-prone guessing = 4. Task slower/suboptimal settings = 3. Cosmetic confusion = 2. Nice-to-know = 1.

**Trust damage** — per Write the Docs: *incorrect docs are worse than missing docs*. Existing page states something now false = 5. Stub/empty page in nav = 4. Recently shipped feature with zero docs (users see it in the UI, search, find nothing) = 4. Feature never documented and not prominent in UI = 2.

**Effort** — 1 = facts already known/small edit; 2 = one page, facts extractable from code; 3 = one page + significant code exploration; 4 = multiple interdependent pages; 5 = needs product decisions or assets we can't produce (e.g., requires login for screenshots).

## Priorities that outrank the formula

1. **A shipped feature that changed documented behavior** — an existing page is now wrong. Fix in the same run even if small (this is the "docs updated?" release gap this skill exists to close).
2. **New customer-facing feature from the commit scan** — document while fresh; freshness is why the skill scans commits at all.
3. Standing backlog below.

## Standing backlog (verified by audit 2026-07-03; re-verify before writing — items get done)

1. **Automations section** — 2 stub files exist out of nav, product fully shipped. Facts (verified): event types in `../revve-web/lib/automation/events.ts` (10 incl. `chat_analyzed`, `call_analyzed`, `lead_created`, `enrollment_*`); operators in `lib/automation/types.ts`; 10 action types in `lib/automation/actions/` (webhook, email, create_ticket, enroll_to_campaign, HubSpot/Salesforce syncs, contact-field updates). Screenshots exist (`automation-*.png`).
2. **Widget SDK reference** — `channel-setup/website-installation.mdx` documents only 4 boot options; `../revve-web/widget/dist/revve.d.ts` (v2) has the full command API: `boot` (userId/email/customAttributes/contact/forceNewThread), `shutdown`, `update`, show/hide, `showNewMessage`, `getAnonymousId`/`getVisitorId`, `onShow`/`onHide`/`onUnreadCountChange`/`onNewMessage`, `showBubble`/`hideBubble`, `setNotificationSound`, plus a deprecated `window.revve` legacy API. Highest developer-credibility win.
3. **Model page rewrite** — `general-configuration/choosing-an-llm-model.mdx` says "OpenAI for all agents" with 3 hardcoded models; reality is DB-driven multi-provider (OpenAI + Claude + Gemini, many models). Rewrite provider-agnostic; don't hardcode a model table.
4. **Zero-coverage products** (confirmed shipped, no docs page): Evaluations (metrics/evaluators/profiles/observability), Apps/Integrations (HubSpot, Salesforce, Calendly, Cal.com, ChiliPiper), Tickets, Contacts (+custom fields), Simulations/batch testing, Settings (members, API keys/secrets, audit logs), Nurturing assets. Each is its own run-sized item; Evaluations and Apps are multi-page.
5. **More recipes** for the Guides group — support agent with human escalation; outbound speed-to-lead campaign (chat capture → API enrollment → voice call); appointment booking voice agent.
6. **API + webhooks reference** — threads, leads, contacts, campaign enrollment, exports; webhook payloads. Large; propose as several runs. **Routes to the `api-reference` skill, not this skill's Phase 3** — it owns endpoint discovery, a human-approval gate (most of `app/api` is internal-only; see its `references/endpoint-discovery.md`), OpenAPI spec authoring, and its own PR.
7. **Knob-opinion rewrites of pre-overhaul pages** — General Configuration pages still enumerate fields without defaults/when-to-change guidance.
8. **Central troubleshooting page** — per-channel troubleshooting now exists inside channel pages; still missing for widget SDK, knowledge retrieval, campaigns, voice agents, integrations. Lower priority.

Resolved (don't re-raise): channel-setup dead ends — all five channel pages now have real setup steps, settings tables, and troubleshooting sections; the remaining "contact your Revve team" callouts reflect genuine admin-side provisioning.

## Anti-patterns

- Don't bundle three unrelated one-point gaps to fill a PR — a themed PR reviews faster than a grab bag.
- Don't pick a 5-effort item for a routine run; split it and put the split in the backlog table.
- Don't rewrite healthy pages because they could be marginally better — routine runs fix gaps, not taste.
