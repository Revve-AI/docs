# Screenshot Capture Workflow

Authenticated capture from the live app at app.revve.ai, proven 2026-06-11. Run this from the **main agent** (it needs the browser and Gmail); writers never log in.

## Production-safety rules (absolute)

You are navigating a **production** system with real customer data.

- Navigation, tab clicks, and screenshots only. Never publish, save, delete, enroll, send, or create anything.
- If a screenshot requires an *editing* state (e.g. a campaign's draft banner): acquire the lock, capture, then immediately click **Stop Editing** to release it. Never leave a screen holding a lock.
- Dialogs needed for a shot (e.g. "New Voice Agent"): open, capture, close with **Escape** — never the confirm/create button.
- If a screen would expose customer PII prominently, prefer a screen with the team's own test data, or skip the shot.

## Authentication (magic link — the only reliable path)

Saved cookies/state don't survive: Supabase rotates refresh tokens, so any stored auth state is dead within days. Sign in fresh each run:

1. Start the browser: `agent-browser set viewport 1440 900`, then `agent-browser open "https://app.revve.ai/signin"`.
2. `agent-browser snapshot -i`, fill the email box with `trung@revve.ai`, click **Get Sign-in Link**.
3. Read the link from Gmail with the `gws` CLI (its keyring auth works on this machine; the claude.ai Gmail MCP token may be expired):
   ```bash
   gws gmail users messages list --params '{"userId":"me","q":"newer_than:1h subject:magic","maxResults":3}'
   gws gmail +read --id <newest-id>
   ```
   The body contains `https://s.revve.ai/auth/v1/verify?token=pkce_...&type=magiclink&redirect_to=...`.
4. Open that URL **in the same agent-browser session that requested it** — it's a PKCE flow; the code verifier lives in that browser session. Opening it elsewhere fails.
5. You land on `/dashboard/<teamSlug>` signed in.

If sign-in fails twice, stop trying: fall back to the PR-body "Missing screenshots" list per SKILL.md Phase 4.

## Known app quirks

- Team slug for trung@revve.ai: `8da5a5766e5edcc530fc` (has realistic data: agents, a live campaign).
- Voice agents live under `/callbots`, chat agents under `/chatbots`.
- Chat agent **Preview** tab: `/preview` is the SMS-only preview; website agents use `/preview-website`.
- `agent-browser state load` fails while the daemon is running — don't bother with saved state; magic link every time.
- If `agent-browser` complains about a missing Playwright browser, install with the CLI's own bundled version: `cd $(dirname $(readlink -f $(which agent-browser)))/.. && node node_modules/playwright-core/cli.js install chromium-headless-shell`.

## Capture conventions

- Viewport 1440×900; full-window `agent-browser screenshot /Users/trungvu/dev/revve/docs/screenshots/<name>.png`.
- Names: feature-prefixed kebab-case matching existing files — `voice-*`, `campaign-*`, `chatbot-*`, `flow-node-*`, `knowledge-*`.
- Give the page a beat to settle before capturing (`agent-browser wait --load networkidle` plus ~2s).
- **Always Read the captured PNG afterward** and check it shows what the doc's alt text claims — wrong-state screenshots are worse than none. Re-capture if a toast, spinner, or the Ask-Revve dock obscures the subject.
- Replacing an outdated screenshot: overwrite the same filename so existing pages pick it up; new states get new names.

## Wrap-up

- `agent-browser close` when done.
- Delete any magic-link emails? No — leave the inbox untouched beyond reading.
- List every shot you captured (and any you couldn't) in your run report and the PR body.
