# Ajaia Docs — frontend

React (Vite) + TipTap single-page app for the Ajaia Docs editor.

See the [root README](../README.md) for full setup, run, and deploy
instructions. Quick start:

```bash
npm install
npm run dev     # http://localhost:5173 (proxies /api to the backend on :8001)
```

- `npm run build` — production build to `dist/`
- `npm run lint` — oxlint

Set `VITE_API_BASE_URL` (see `.env.example`) only for production builds where
the API is on a different origin. Locally the dev proxy handles it.
