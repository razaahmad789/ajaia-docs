# AI workflow note

This is an AI-forward role, so I worked AI-native from the first minute — but
kept judgment, verification, and architecture decisions my own. Below is an
honest account of where AI helped, what I rejected, and how I checked the work.

## Tools used

- **Claude Code (Claude Opus)** as the primary pair-programmer: scaffolding
  Django/DRF and React, drafting the TipTap integration, boilerplate for
  serializers/views/tests, and the first drafts of these docs.
- **Playwright** (driven headlessly) for end-to-end UI verification and
  screenshots.
- Standard non-AI tooling as the ground truth: Django's test runner, `oxlint`,
  `manage.py check --deploy`, and reading library source in `node_modules`.

## Where AI materially sped me up

1. **Boilerplate-heavy surfaces.** DRF serializers/viewset wiring, the token
   login view, the management command to seed data, and the React API client +
   context providers are the kind of code that's tedious to type and easy to
   get *mostly* right — AI got me to a working draft in minutes.
2. **The editor integration.** TipTap's API surface (commands, `isActive`
   states, the toolbar) is a lot of small correct calls; AI assembled the
   toolbar and editor component quickly.
3. **Docs and tests from a working baseline.** Once the behavior was settled,
   AI drafted the test matrix and the README/architecture notes, which I then
   edited for accuracy and tone.

Net: AI compressed the "typing" parts so I could spend the timebox on the
decisions that actually matter — the data model, access control, and what to
cut.

## What I changed or rejected from AI output

- **Rejected double-registering TipTap extensions.** The first draft imported
  `@tiptap/extension-underline` and `-link` *and* used StarterKit. I checked
  `node_modules/@tiptap/starter-kit` and confirmed v3 already bundles both —
  adding them again would throw duplicate-extension warnings. I removed the
  extra packages and configured them through StarterKit instead.
- **Hardened content handling.** I didn't trust editor/imported HTML. I added a
  server-side **bleach** allow-list and made *every* write path sanitize, then
  wrote tests proving `<script>` / `onerror=` are stripped. This was a
  deliberate security decision, not a default.
- **Fixed a deploy footgun.** An early config turned on Django's
  `SECURE_SSL_REDIRECT` in production. On Render, TLS terminates at the edge and
  the internal health check is plain HTTP — an app-level redirect can fail the
  health check. I turned it off by default (opt-in via env) and documented why.
- **Simplified over-clever code.** An AI-suggested undo/redo handler wrapped the
  command in a needlessly indirect closure; I rewrote it as a direct
  `editor.chain().focus().undo().run()`.
- **Chose the import design myself.** Rather than storing uploaded files, I had
  import parse in memory and persist only the resulting document — avoiding
  fragile media storage on an ephemeral free-tier disk. AI implemented the
  parser; the architectural call was mine.

## How I verified correctness, UX, and reliability

- **Correctness (logic/security):** 21 automated tests focused on the risky
  parts — sharing access control (viewer can't edit, non-shared user gets 404,
  only owner deletes/shares), sanitization, and import. All pass.
- **UX quality:** I ran the real UI end to end with Playwright against the live
  dev servers — login, create/edit, **bold** actually produces `<strong>`,
  autosave reaches "All changes saved", the **viewer** is genuinely read-only
  (`contenteditable=false`, toolbar disabled, no Share button), and `.md`
  import yields a parsed `<h1>`/`<strong>` document. Zero console errors.
  Screenshots are in `docs/screenshots/`.
- **Reliability/deploy:** `manage.py check --deploy` (remaining warnings are
  intentional and explained), a clean `vite build`, `collectstatic` with the
  production manifest storage, and a `render.yaml` whose build step runs
  migrations + seed.

## Principle

I treated AI as a fast, fallible collaborator: great for drafts and breadth,
but every security boundary, data-model decision, and "is this actually
working?" question was verified with tests, a real browser, or by reading the
source — never taken on faith.
