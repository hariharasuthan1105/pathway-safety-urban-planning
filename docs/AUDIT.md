# Rebuild audit — 2026-10-13

VERIFIED: `git fetch origin --prune` advanced main to `4d3a731`. The trees of
`857df4e` and `4d3a731` are identical (`git diff … --stat` empty), as are
`e83fcba` and `169e4c2`. The feature commits were squash merged, not direct
ancestors. `5857851` is an ancestor. `gh pr list --state open` returned `[]`.
No cherry-picks are necessary. The previous uncommitted Pages fix is preserved
in a named stash and reapplied to `feat/urban-intelligence-rebuild-v2`.

INFERRED from inspected source:
- Entry: `frontend/index.html` → `src/main.tsx` → `src/app/App.tsx`.
- Landing/login and `/app/digital-twin` mount the same lazy voxel CityScene.
  Protected overview, cities, traffic, risk, environment, events, copilot and
  settings routes share AuthProvider and TelemetryProvider. Pages uses HashRouter.
- `python -m src.main` starts FastAPI through `src/webhook_server.py`, binds
  0.0.0.0 using PORT, and runs the Pathway processing graph.
- Connectors → schema tables → combined stream → anomaly transforms →
  subscription sink → shared CityStateManager/RAG → protected API/SSE.
- SQLite auth uses AUTH_DB_PATH, PBKDF2 passwords, expiring sessions, cookies
  and a supported bearer header. Logout currently revokes only cookie sessions.
- `/api/health` is public; `/api/state`, `/api/stream`, history, risk, anomalies,
  events and copilot require authentication. `/events` validates webhook secrets,
  coordinates, size, rate and deduplication. In-memory data is lost on restart.
- CI has compatibility, native Pathway and frontend jobs. Pages publishes only
  `frontend/dist`; root legacy files were removed by PR #3.

## Deletion review

| File | Evidence / action |
|---|---|
| root index.html, script.js, style.css | Already deleted on main in PR #3. Historical docs still mention them; no new deletion needed. |
| components/{ai-assistant-dashboard,dashboard-content,dashboard-header,dashboard-sidebar}.tsx | Already deleted in PR #3. |
| frontend/src/App.tsx, App.css, assets/{hero.png,react.svg,vite.svg} | Vite starter only. main.tsx imports app/App. VERIFIED rg across source, workflows, tests and docs: only starter self-imports and historical docs. Removed these five files; active main imports app/App. |

VERIFIED tooling: local Node v24.19.0, Python 3.12.14, gh available.
UNVERIFIED locally: Node 22, native Linux Pathway; WSL reports missing runtime,
Docker is not installed. These require Linux CI. The supplied voxel image is in
conversation context; existing geometry is retained rather than regenerated.

This is a code audit, not a claim of deployed behavior or hosted auth support.
