# Architecture note

A short account of what I built, the decisions behind it, and what I
deliberately cut under the 4–6 hour timebox.

## Priorities (in order)

1. **Depth in the three "product" surfaces** the brief weights most: the
   editing experience, file import, and sharing — with *correct* access
   control rather than a mock.
2. **A testable, deployable slice.** Real auth tokens, a real database, real
   migrations, automated tests, and a one-command deploy.
3. **Security hygiene** appropriate to a document product: everything that
   renders user HTML is sanitized, and access rules are enforced on the server,
   not just hidden in the UI.

Everything else (real-time co-editing, `.docx`, version history, a signup flow)
was consciously postponed — see the last section.

## Stack and why

| Choice | Why |
|---|---|
| **Django + DRF** | The brief has users, sharing, uploads, and persistence — exactly what Django gives "for free" (auth, ORM, migrations, admin, a mature test client). That bought time to spend on the editor and sharing instead of plumbing. |
| **React (Vite) + TipTap** | TipTap is a ProseMirror wrapper: a real document model (not `contentEditable` soup), with the formatting the brief asks for already in its StarterKit. Vite keeps the dev loop fast and builds a static bundle that deploys anywhere. |
| **Token auth (seeded users)** | A simple, demoable login that makes owned-vs-shared obvious, without spending the timebox on registration/password-reset flows. |
| **SQLite → Postgres** | Zero-config locally, durable in production. `dj-database-url` switches via one env var, so the code is identical in both. |

## Data model

Three tables (plus Django's `User` and DRF's `Token`):

- **Document** — `id` (UUID), `title`, `content` (HTML), `owner` (FK), timestamps.
- **Share** — `document` + `user` + `role` (`viewer` | `editor`), unique per
  (document, user). This *is* the sharing model.
- The **owner** is a role too, represented by `Document.owner` rather than a
  Share row, so there's always exactly one owner.

`Document.role_for(user)` collapses all of this into one of
`owner | editor | viewer | None`, and the API and UI both key off it.

### Why content is sanitized HTML (not ProseMirror JSON)

TipTap round-trips HTML cleanly (`editor.getHTML()` ↔ `content`), and the
Markdown/plain-text import path also produces HTML — so **one representation**
serves create, edit, and import. The cost of accepting HTML is XSS risk, so
every write path runs it through **bleach** against a small allow-list of tags
(`backend/documents/sanitize.py`). ProseMirror JSON would be "more correct" but
would need conversion on import and on render, for no user-visible gain here.

### Why import stores no file

The import feature parses the upload **in memory** and persists only the
resulting document. That means no media volume, no S3, and nothing to lose on
an ephemeral free-tier disk — the imported content lives in the same durable
place as every other document. (Storing the original file as an *attachment*
is a reasonable alternative; it's in the "next" list.)

## Access control (the part worth getting right)

Enforced server-side in two layers:

1. **Queryset scoping** — `get_queryset()` returns only documents you own or
   that are shared with you. A stranger requesting a document by id gets **404**
   (we don't leak existence), not 403.
2. **Object + action permissions** — `DocumentAccessPermission` allows read for
   any role, write only for owner/editor, and delete only for the owner.
   Sharing endpoints re-check owner explicitly.

The UI mirrors these (disabled toolbar for viewers, no Share/Delete buttons),
but the UI is a convenience — the server is the source of truth. The sharing
and permission rules are the most heavily tested part of the codebase.

## Editing & autosave

The editor emits HTML on change; the page debounces writes (~900 ms) and
`PATCH`es the document, showing a "Saving… / All changes saved" status. Saves
are **last-write-wins** — correct for single-author editing and the realistic
case here. True concurrent editing needs CRDT/OT and a socket, which is out of
scope (below).

## Testing strategy

The brief asks for *at least one* meaningful test; I wrote 21, concentrated
where a bug would be a real product or security problem:

- **Sharing/access control** — viewers can't edit, non-shared users can't read,
  only owners delete/share, re-sharing updates the role, revoke works.
- **Sanitization** — `<script>` and `onerror=` are stripped on create and import.
- **Import** — Markdown → HTML structure, plain-text → paragraphs, bad types
  rejected.

I also ran the full flow headlessly (Playwright against the real UI) to confirm
the editor renders, formatting applies, autosave fires, the viewer is read-only,
and import works — screenshots are in `docs/screenshots/`.

## What I'd build next (with 2–4 more hours)

- **Real-time collaboration** — presence indicators first (cheap, high signal),
  then Yjs/CRDT for true concurrent editing. The current autosave is the
  honest single-writer version.
- **`.docx` import** via `mammoth`, reusing the same sanitize-then-store path.
- **Version history** — snapshot on save; a lightweight revisions table.
- **Self-serve accounts** — registration + a proper "share with anyone by
  email (invite)" instead of seeded users only.
- **Attachments** — keep the original uploaded file alongside the document
  (needs object storage on the host).
