# Ajaia Docs — a lightweight collaborative document editor

A Google-Docs-inspired app for creating, editing, importing, and sharing
rich-text documents. Built for the AI-Native Full Stack assignment with a
deliberately narrow, deep scope.

- **Backend:** Django 4.2 + Django REST Framework (token auth)
- **Frontend:** React (Vite) + TipTap (ProseMirror) rich-text editor
- **Database:** SQLite locally, PostgreSQL in production
- **Deploy:** Render (API web service + Postgres + static site)

> Live demo URL and video link are in [`SUBMISSION.md`](./SUBMISSION.md).

---

## What it does

| Capability | Details |
|---|---|
| **Create / rename / edit** | Rich text: bold, italic, underline, strikethrough, H1–H3, bullet & numbered lists, blockquote, code block. Changes **autosave** (debounced). |
| **Persist & reopen** | Documents and shares persist in the database and survive refresh. Content is stored as sanitized HTML. |
| **File upload (import)** | Upload a **`.txt` or `.md`** file → it becomes a new editable document (Markdown is converted to HTML, then sanitized). Supported types are shown in the UI. |
| **Sharing** | Each document has an **owner**. The owner shares by email with a **Viewer** (read-only) or **Editor** (can edit) role. The dashboard separates **Owned by me** from **Shared with me**. |
| **Access control** | Enforced server-side: non-shared users get 404; viewers can't edit; only owners can delete or manage sharing. Covered by automated tests. |

### Demo accounts (seeded)

| Email | Password | Role in demo |
|---|---|---|
| `alice@example.com` | `password123` | Owns "Welcome to Ajaia Docs", shared with Bob & Carol |
| `bob@example.com` | `password123` | **Editor** on Alice's doc; owns a private "Q3 Roadmap" |
| `carol@example.com` | `password123` | **Viewer** (read-only) on Alice's doc |

Log in as Alice to share/edit; open the same doc as Carol to see read-only access.

---

## Run locally

**Prerequisites:** Python 3.9+ and Node 18+ (built with Python 3.9, Node 24).

### 1. Backend (Terminal 1)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed               # creates the demo users + documents
python manage.py runserver 127.0.0.1:8001
```

The API is now at `http://127.0.0.1:8001/api/`.

### 2. Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api` to the
backend on port 8001 (see `frontend/vite.config.js`), so no CORS setup or
env vars are needed locally. Sign in with a demo account above.

> If your backend runs on a different port, set
> `VITE_DEV_API_TARGET=http://127.0.0.1:<port>` before `npm run dev`.

### Run the tests

```bash
cd backend
source .venv/bin/activate
python manage.py test
```

21 tests cover auth, sharing access control, content sanitization, and import.

---

## How the pieces fit

```
frontend (React + TipTap)  ──HTTP (token auth)──►  backend (Django REST)
   localhost:5173                                       localhost:8001
   - editor, autosave                                   - Document / Share models
   - owned vs shared lists                              - object-level permissions
   - share dialog, import                               - HTML sanitization
                                                        - .txt/.md import
                                                              │
                                                              ▼
                                                   SQLite (dev) / Postgres (prod)
```

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for decisions and tradeoffs, and
[`AI_WORKFLOW.md`](./AI_WORKFLOW.md) for how AI was used.

### API surface (brief)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/auth/login/` | Log in by email+password → `{ token, user }` |
| `GET` | `/api/me/` | Current user |
| `GET/POST` | `/api/documents/` | List (owned + shared) / create |
| `GET/PATCH/DELETE` | `/api/documents/{id}/` | Retrieve / update / delete |
| `POST` | `/api/documents/import/` | Create a document from an uploaded `.txt`/`.md` |
| `GET/POST` | `/api/documents/{id}/shares/` | List shares / grant access by email |
| `DELETE` | `/api/documents/{id}/shares/{shareId}/` | Revoke a share |
| `GET` | `/api/health/` | Health check |

Authenticated requests send `Authorization: Token <key>`.

---

## Deploy (Render)

This repo ships a `render.yaml` Blueprint (API + Postgres + static frontend).

1. Push this repo to GitHub.
2. In Render: **New + → Blueprint**, select the repo. It creates the database,
   the `ajaia-docs-api` web service, and the `ajaia-docs-web` static site.
3. You'll be prompted for a few `sync: false` values on first apply. After the
   services get their URLs, set these (full `https://` URLs, **no trailing slash**):
   - On **ajaia-docs-api**: `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`
     = the frontend URL, e.g. `https://ajaia-docs-web.onrender.com`
   - On **ajaia-docs-web**: `VITE_API_BASE_URL` = the API URL, e.g.
     `https://ajaia-docs-api.onrender.com`
4. Redeploy the frontend after setting `VITE_API_BASE_URL` (Vite inlines it at
   build time). The backend's `build.sh` runs migrations and seeds demo users
   automatically.

Notes:
- Render's **free** Postgres expires ~30 days after creation, and free web
  services **spin down when idle** (the first request after idle is slow).
- `DJANGO_SECRET_KEY` is generated by Render; `DJANGO_DEBUG=False` in prod.

---

## Scope & limitations

**Working end to end:** auth, document CRUD, rich-text editing with autosave,
`.txt`/`.md` import, role-based sharing (viewer/editor), owned-vs-shared
separation, server-side access control, sanitization, tests, and deployment.

**Intentionally deprioritized** (and what I'd do next) — see
[`ARCHITECTURE.md`](./ARCHITECTURE.md#what-id-build-next-with-24-more-hours).
Briefly: real-time multi-user editing (this uses last-write-wins autosave, not
CRDT/OT), `.docx` import, version history, and a full registration flow.
