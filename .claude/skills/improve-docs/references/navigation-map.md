# Navigation Map

Single source of truth for where content lives in `docs.json`. Consulted by
Phase 1 Agent C (audits the docs against this target structure), Phase 2
(the "Proposed page(s)" column should cite a destination from this map), and
the Phase 3 editor pass (the only pass allowed to touch `docs.json`).

As of the 2026-07 nav restructure, `docs.json` uses `navigation.tabs`, not
`navigation.groups` — each tab holds an ordered list of groups, and a group's
`pages` array can itself contain a nested `{ "group": ..., "pages": [...] }`
object to scope a subsection (Mintlify supports groups-within-groups).

## Tab: Documentation

One journey-ordered sidebar. Persona routing happens on `introduction.mdx`,
not via separate tabs — SMB owners wear every hat, so splitting the sidebar
by persona would force them to keep switching tabs.

| # | Group | Folder(s) | Charter — what belongs here |
|---|-------|-----------|------------------------------|
| 1 | Getting Started | `getting-started/` | First-run orientation: what Revve is, quickstart, publishing/versioning basics. Not feature-specific how-tos. |
| 1b | Ask Revve | `ask-revve/` | The in-app AI copilot: the dock/dashboard-home chat, page context, direct actions, the propose-then-Apply-to-draft flow, and Skills (copilot instruction modules — NOT customer-agent config). Sits right after Getting Started because the dashboard home is the copilot. Added 2026-07-04. |
| 2 | Recipes | `guides/` | End-to-end, copy-paste-able recipes for one complete use case (qualify a lead, run a payment-reminder campaign, book an appointment by voice). |
| 3 | Voice Agents | `voice-agents/` | Everything specific to phone-call agents: creation, settings, evaluation, tools, call transfer, do-not-call, publishing/versioning. Comes before Chat Agents (owner priority — voice is the higher-intent, higher-cost surface). |
| 4 | Chat Agents | `getting-started/` (chat concept pages) + `general-configuration/` + nested `conversational-flow/` | Everything specific to text-channel agents: what a chat agent is, creating one, engine types, identity/model/welcome-message/tone configuration, and the nested **Conversation Flow** subgroup for the flow-editor pages. New chat-agent configuration pages keep landing in `general-configuration/` even though the nav label is "Chat Agents" (see placement rule 4). |
| 5 | Knowledge Base | `knowledge-base/` | Content ingestion and retrieval: overview, adding sources, FAQs, gaps, settings. Shared by chat and voice agents. |
| 6 | Channels | `channel-setup/` | Per-channel connection setup: website widget (appearance, installation, bubble messages), email, SMS, WhatsApp, Zalo, Messenger. |
| 7 | Campaigns | `campaigns/` | Outbound campaign creation, enrollment management, versioning. |
| 8 | Evaluations | `evaluations/` | Pre-ship regression testing shared by chat and voice agents: evaluators, the team-wide metrics library, the create-run-inspect loop. Shipped 2026-07 (PR #12); sits directly after Campaigns. Future pages (profiles, scorecards, batch runs, simulations) land in this same group/folder. |
| 9 | Inbox & Operations | `inbox/` | Day-to-day conversation handling: inbox overview, managing conversations, filtering/searching, the conversation analysis panel, human takeover. |
| 10 | History & Analytics | `history-analytics/` | Looking backward: chat history, exports, analytics dashboard, daily reports. |
| 11 | Administration | `governance-access/` (today) + future `administration/` | Workspace-level control: roles/permissions, publish-approval workflow, and (future) settings pages. |

## Tab: Developers

| Group | Source | Charter |
|-------|--------|---------|
| API Reference | `openapi: api-reference/openapi.json` | The generated REST API reference (customer-facing endpoints only, gated by the `api-reference` skill's approval process). |

## Future groups (not in `docs.json` yet — add only with a first real page)

These are pre-approved destinations so a writer never has to invent nav
structure mid-run. A group appears here whether or not any page exists for
it yet; it does **not** appear in `docs.json` until it has real content.

| Future group | Folder | Target position | Notes |
|---|---|---|---|
| Automations | `automations/` | Between Campaigns and Evaluations (i.e. Campaigns → Automations → Evaluations → Inbox & Operations) | Two stub files already exist (`automations/automation-rules-overview.mdx`, `automations/creating-automation-rules.mdx`) but are intentionally out of nav and listed in `scripts/known-orphans.txt` until they get real content — do not fill them as part of a nav-only change. |
| Integrations | `integrations/` | After History & Analytics | One setup page per third-party app: calendars, HubSpot, Salesforce, Slack, etc. |
| Tickets | `tickets/` | New pages under Inbox & Operations | Ticketing surface adjacent to the inbox. |
| Contacts | `contacts/` | New pages under Inbox & Operations | Contact records and custom fields. |
| Developer Guides | `developers/` | New group in the Developers tab, alongside API Reference | Widget SDK reference, webhook event reference, authentication/API keys. |

### Already-shipped subgroups to keep in mind

- **Voice Agents → Conversation Flow**: if/when the voice flow engine gets
  its own pages (distinct from the chat `conversational-flow/` pages), they
  nest under Voice Agents the same way chat's Conversation Flow nests under
  Chat Agents. Folder: `voice-agents/` (or a new `voice-agents/flow/`
  subfolder if the page count warrants it — decide at write time).
- **Administration → workspace settings**: brand, block/whitelist, limits,
  routing, custom fields, alerts, secrets, audit logs, phone numbers. All
  land in `administration/` and nest under the Administration group.

## Placement rules

1. **Prefer an existing group.** Adding a page to a group already in this
   map (shipped or future) is always preferred over inventing a new one.
   Creating a group that isn't in this map requires adding it here first —
   in its own edit, reviewed like any other structural change.
2. **A group enters `docs.json` only with its first real page.** Never ship
   an empty group or a stub page into nav. (Automations is the running
   example: real files on disk, deliberately absent from nav and tracked in
   `scripts/known-orphans.txt` instead.)
3. **Never move or rename existing files.** URLs derive from file paths, not
   nav position or labels — moving a file breaks external links and search
   results. If a move is ever genuinely unavoidable, add a `redirects` entry
   in `docs.json` in the same change.
4. **Chat-agent configuration pages keep the `general-configuration/`
   folder** even though the nav group is called "Chat Agents" — the folder
   name is a historical artifact of the old flat nav, not a target to
   rename.
5. **Nav edits happen only in the editor pass**, never inside a parallel
   writer subagent's scope. Writers propose a destination page path;
   deciding where it sits in `docs.json` is the editor's job, done once,
   serially, against this map.
