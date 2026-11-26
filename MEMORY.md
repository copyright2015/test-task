# Project progress and handoff

This file is the durable project handoff. Read it before continuing implementation and update it when project status or important decisions change.

## Current state

Initial working application skeleton has been implemented from `PRD.md`, `ARCHITECTURE.md`, `DESIGN.md`, `RULES.md`, and `TASKS.md`.

- Backend: FastAPI + SQLAlchemy 2, Keitaro HTTP client, SQLite cache, Alembic migrations.
- Frontend: Vue 3 + Vuetify, Vue Router, Vue I18n (English/Russian), light/dark theme switch.
- Pages: campaign list, campaign creation, campaign editor.
- Launch scripts: `run.bat` and `run.sh`; they check Python 3.10+ and Node.js 18+, set up dependencies and migrations, then start both services.
- Database tables: `campaigns`, `offers`, `streams`, `stream_offers`, and seeded `countries`.
- Keitaro key is read from `KEITARO_API_KEY`; configure it in a local `.env` copied from `.env.example`. Never commit the key or put it in frontend code.

## Implemented behavior

- Campaign list reads its initial contents from SQLite and has an explicit refresh-from-Keitaro action. Enable/disable and delete operations call Keitaro.
- Campaign creation selects a country and an API offer, then creates the campaign and two streams (country redirect to Google and selected offer). It selects the first available domain, campaign group, and traffic source from the API.
- Editor loads campaign and streams from Keitaro, supports stream and offer additions/removals, offer restoration, fixed shares, and submits edits explicitly.
- Existing streams with no active or archived offers show only their name and delete action. New streams and streams with archived offers retain their offer controls.
- The editor highlights modified and removed stream cards, enables saving only when changes exist, and prompts before leaving with unsaved changes. Browser refresh/close uses the browser's native warning.
- Removing an existing stream marks its card for deletion until saving and allows restoring it; a new unsaved stream is removed immediately.
- Removed stream offers are retained in `stream_offers` as inactive records to support restoration.
- Removed offers in the editor use a muted row style adapted to the current theme; the restore button remains available.
- UI strings are in `frontend/src/locales.js`; theme colors are in `frontend/src/theme.js`.
- `README.md` contains both Russian and English setup instructions.
- Vuetify components require `vite-plugin-vuetify` with `autoImport: true` in `frontend/vite.config.js`; without it, the Vue tags render as unstyled custom elements.
- The campaign editor response must serialize the fetched `campaign` object (not an undefined variable); frontend API parsing accepts text responses so non-JSON server errors remain readable.

## Verification completed

- `npm run build` in `frontend/` passed.
- `python -m compileall -q backend\app backend\migrations` passed.
- `python -m alembic -c backend\alembic.ini upgrade head` passed; migration seeds 22 country codes.
- FastAPI local checks passed for `/api/health` and the local campaign list. `/api/catalog` correctly reports 503 when no API key is configured.
- `git diff --check` passed.
- Keitaro live API calls have **not** been verified with credentials.
- `npm install` reported 6 dependency audit findings (1 moderate, 5 high); they were not auto-fixed.
- Verified the rendered app in a browser after enabling Vuetify auto-import: navigation, app bar, themed controls, and campaign action buttons render as Vuetify components.
- Reproduced and fixed a 500 on the editor route; verified the API now returns campaign/stream data and the editor renders those streams in the browser.
- Verified editor change detection in the browser for stream renaming, adding/removing a new stream, and removing/restoring an offer; reverting each change disables saving again.
- Verified that an existing stream without offers is compact, while new streams and streams containing removed offers retain offer controls.
- Verified card highlights, stream deletion/restoration, the leave dialog, failed and successful saves, route changes, and the `beforeunload` event using mocked API responses in the browser.
- Browser test pages with mocked `fetch` must be closed after verification: their test data persists across reloads in that page and can be mistaken for real data.

## Next steps / caveats

1. Configure a valid `KEITARO_API_KEY` locally and smoke-test catalog retrieval, campaign creation, stream editing, enable/disable, and deletion against the test API.
2. Verify Keitaro's actual test-server schema for domain/group/source field names and stream filter/action payloads. The public OpenAPI docs were checked during initial work, but the specified test API may differ.
3. Add focused automated tests for backend API payload construction and offer share/restore behavior.
4. Reassess dependency audit findings before release.

The implementation is an initial baseline, not a fully validated production release. Preserve unrelated worktree changes; the initial project Markdown files were untracked when implementation started.