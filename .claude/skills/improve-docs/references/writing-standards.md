# Revve Docs Writing Standards

These conventions come from the 2026-06/07 docs overhaul (competitor analysis of Retell / ElevenLabs / Vapi + the Write the Docs principles). Follow them so every new page reads like part of one system.

## The core principle

The old docs failed as "an outdated list of features & knobs — not actionable". Every page must answer **what should I do and why**, not "what does each field say". Concretely:

- Start from a user goal, never from a UI screen inventory.
- Document what runs in **production** (`origin/prod` of the product repos), not dev branches or local checkouts.
- Voice agents: when the UI differs by provider, document the **Revve provider** path (`provider === 'revve'`: tabs Dashboard / General / Model Settings / Knowledge Base / Advanced Settings / Evaluation / Preview / Versions — see `CallBotNav.tsx`). Legacy Retell-provider agents show different tabs (Prompt / Speech Setting / Call Setting); don't document those.
- Every setting gets an opinion: its **default**, **when to change it**, and the **trade-off**. Pattern to imitate (from `voice-agents/voice-agent-settings.mdx`): "Callers getting cut off → raise toward 0.8–1.0s. Agent feels sluggish → lower toward 0.4s."
- Prefer "in full, or not at all": a half-written page erodes trust more than no page. Never commit a stub.
- Outdated is worse than missing. Ground every UI label, default, and field name in the product code or a current screenshot. If unverifiable, omit it.

## Page templates

**Concept page** ("What is X?") — what it is in one paragraph → how it works (numbered mechanics) → capabilities table → key concepts → when to use it (use-case table) → What's Next. Example: `campaigns/campaign-overview.mdx`.

**How-to page** ("Creating your first X") — outcome promise in the intro → `## Step N: <verb phrase>` sections → each step: exact UI labels in **bold**, one screenshot, a Tip for the judgment call → ends with the thing working → What's Next. Example: `voice-agents/creating-your-first-voice-agent.mdx`.

**Settings page** — grouped by real UI tabs/sections, tables with columns `Setting | Default | When to change` → a closing "tuning workflow" section. Example: `voice-agents/voice-agent-settings.mdx`.

**Recipe/guide** — "What you'll build" + time estimate → prerequisites → numbered steps with **complete copy-paste prompts/configs** (bracketed `[placeholders]` for the reader's business) → a test-scenario table → variations. Example: `guides/lead-qualification-agent.mdx`.

## Formatting conventions

- Frontmatter: `title` + `description` only. Note the blank line after `---` used by existing pages.
- Mintlify components in use: `<Tip>`, `<Note>`, `<Info>`, `<CardGroup cols={2}>`/`<Card>`. Tables over `<Steps>`.
- Internal links: absolute paths (`/voice-agents/what-is-a-voice-agent`), never `.mdx` suffixes.
- Screenshots: `![descriptive alt text explaining what the reader should see](/screenshots/kebab-name.png)`. Naming: feature-prefixed kebab-case (`voice-*`, `campaign-*`, `flow-node-*`). Standard capture: 1440×900.
- End most pages with `## What's Next` linking 2 related pages.
- UI labels in **bold**, exactly as rendered in the app ("**+ New Voice Agent**", "**Start Editing**").

## MDX gotchas (these have bitten us)

- **Raw `{{variable}}` outside backticks silently blanks the entire page body** (parsed as a JSX expression; the TOC still renders, so it looks half-working). Always write template variables as `` `{{firstName}}` ``.
- Raw `<` followed by a letter starts a JSX tag — write `&lt;` or backtick it.
- Duplicate headings on one page break anchor links.

## Verification before committing (all required)

```bash
mint broken-links                 # must print "success no broken links found"
grep -rn '{{' <new files>         # every hit must be inside backticks/code fences
# nav check: every page in docs.json navigation.groups has a file, no accidental orphans
# image check: every /screenshots/*.png referenced by changed pages exists
```

If feasible, render-check each new page with `mint dev` and confirm the body isn't empty (the double-brace failure mode).

## Voice and tone

Direct, confident, second person. Short sentences. Explain the *why* behind recommendations ("it caps cost when a call goes nowhere"). No marketing filler, no "simply", no exclamation-mark enthusiasm — one 🎉 at the end of the quickstart is the sanctioned lifetime supply.
