# Submission — Ajaia Docs

Collaborative rich-text document editor (Google-Docs-inspired) for the
AI-Native Full Stack Developer assignment.

## Links

| Item | Link |
|---|---|
| **Live product** | _TODO: paste Render frontend URL, e.g. https://ajaia-docs-web.onrender.com_ |
| **Walkthrough video (3–5 min)** | _TODO: paste unlisted Loom/YouTube link_ (also in `VIDEO.md`) |
| **Source code** | This repository / Drive folder |

## Review credentials (seeded)

All passwords: `password123`

| Email | Use for |
|---|---|
| `alice@example.com` | Owner — edit, share, delete; owns a doc shared with Bob & Carol |
| `bob@example.com` | Editor on Alice's doc; owns a private doc |
| `carol@example.com` | Viewer (read-only) on Alice's doc |

**Fastest way to see sharing:** log in as **Alice**, open "Welcome to Ajaia
Docs", click **Share**; then log in as **Carol** and open the same doc to see
read-only access.

## What's included

| File / folder | Contents |
|---|---|
| `README.md` | Setup, local run, test, and deploy instructions; API overview |
| `ARCHITECTURE.md` | Design decisions, tradeoffs, and what I'd build next |
| `AI_WORKFLOW.md` | AI tools used, what I changed/rejected, how I verified |
| `SUBMISSION.md` | This file |
| `VIDEO.md` | Walkthrough video link |
| `render.yaml` | Render Blueprint (API + Postgres + static frontend) |
| `backend/` | Django + DRF API (models, serializers, views, permissions, tests, seed) |
| `frontend/` | React + Vite + TipTap SPA |
| `docs/screenshots/` | Screenshots of each main screen |

## Feature status

**Working end to end**
- Create, rename, edit, save, reopen documents
- Rich text: bold, italic, underline, strikethrough, H1–H3, bullet/numbered
  lists, blockquote, code block; debounced autosave
- File import: `.txt` / `.md` → new editable document (type limits shown in UI)
- Sharing: owner + share-by-email with **Viewer/Editor** roles; owned-vs-shared
  separation; revoke access
- Server-side access control (404 for non-shared, viewers can't edit, owner-only
  delete/share)
- Persistence (SQLite dev / Postgres prod), HTML sanitization
- 21 automated tests; one-command Render deploy

**Intentionally not built (timebox)** — real-time concurrent editing (autosave
is last-write-wins), `.docx` import, version history, self-serve registration,
file attachments. Rationale and a "next 2–4 hours" plan are in `ARCHITECTURE.md`.

## Verify locally in ~2 minutes

```bash
# Backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && python manage.py migrate && python manage.py seed
python manage.py test        # 21 tests
python manage.py runserver 127.0.0.1:8001

# Frontend (new terminal)
cd frontend && npm install && npm run dev   # http://localhost:5173
```
