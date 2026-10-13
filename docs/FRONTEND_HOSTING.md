# GitHub Pages hosting and verification

The frontend host is GitHub Pages. A read-only GitHub API check on 13 October 2026 returned `build_type: workflow` and the public address https://hariharasuthan1105.github.io/pathway-safety-urban-planning/. Earlier branch/root publishing served the obsolete root HTML; that historical diagnosis is recorded in Git history. Do not use those old deployment instructions.

## Active application

`frontend/index.html` → `frontend/src/main.tsx` → `frontend/src/app/App.tsx`. The landing/auth screens and protected `/app/digital-twin` mount `features/three/CityScene.tsx`, using the retained voxel geometry and simulation. The unused Vite starter `src/App.tsx`, `App.css`, and three starter images have been deleted after reference checks. Repository-root legacy frontend files were already removed in merged PR #3.

## Configuration and approved publication

No hosting settings were changed and this feature branch was not published.

1. Revoke the previously exposed Groq key in the provider dashboard. Put any replacement only in the backend environment. Never put secrets in `VITE_*` variables.
2. Review `feat/urban-intelligence-rebuild-v2` and approve merging before publication. Main pushes affecting the frontend or Pages workflow trigger the Pages workflow; merging is therefore a publication decision.
3. In **Settings → Secrets and variables → Actions → Variables**, ensure `VITE_API_BASE_URL=https://urban-intelligence-backend-z869.onrender.com`, without a trailing slash. Its read-only API lookup returned 404 here; configuration could not be confirmed. The workflow fails with the exact setting to fix if it is missing or invalid.
4. **Settings → Pages → Source** must remain **GitHub Actions** (confirmed via API). Workflow builds from `frontend`, publishes only `frontend/dist`, and sets `VITE_BASE_PATH=/pathway-safety-urban-planning/` and `VITE_ROUTER_MODE=hash`.
5. Review backend environment manually: `ENVIRONMENT=production`, `CORS_ORIGINS=https://hariharasuthan1105.github.io`, `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none`. Preserve the existing persistent `AUTH_DB_PATH` and its disk. Backend changes need separately approved deployment; this task changes no Render settings or configuration.
6. After approval, merge and allow the main workflow, or run **Actions → Publish voxel frontend to GitHub Pages → Run workflow → main**. The workflow passes the repository variable explicitly to validation, health check, Vite build, and artifact validation. It requires HTTP 200 with JSON `status: HEALTHY`; four 15-second attempts separated by five seconds bound cold-start retries to approximately 75 seconds. Never bypass this gate.
7. Verify the actual hosted app after publication: hashed project-path assets, voxel station/airport/buses, direct `/#/login` refresh, signup/login/logout, expired sessions, CORS and SSE in all three browsers. Public `/api/health` returned HTTP 200 HEALTHY on 13 October 2026 at 17:52:12 IST. This point-in-time health result does not verify the new backend authentication code or future uptime.

## Local verification

Use the existing repository and feature branch, preserving local changes. For development set `VITE_API_BASE_URL=http://127.0.0.1:10003`; run backend `python -m src.main` with `PORT=10003`, a disposable `AUTH_DB_PATH`, and CORS origins for ports 5176 and 5177. Run `npm ci` and `npm run dev -- --port 5176 --strictPort` in `frontend`; set `PLAYWRIGHT_BASE_URL=http://127.0.0.1:5176` for `npm run test:e2e` and `npm run test:cross`.

Production builds require an absolute HTTPS origin even during local verification. To test the compiled Pages artifact safely, build with the public origin (or `https://backend.example.test` in CI), the Pages base path, and hash router. Run preview on 5177, then `npm run test:pages` with the same `VITE_API_BASE_URL`, `PLAYWRIGHT_PAGES_URL=http://127.0.0.1:5177`, and `TEST_API_ORIGIN=http://127.0.0.1:10003`. These tests intercept API requests and forward mutations only to the isolated local backend. They do not create public accounts or prove hosted authentication.

`node scripts/verify-artifact.mjs` checks the compiled API origin, loopback absence, and project asset paths. React Router's unused URL-parser fallback uses the reserved `router.invalid` sentinel in production; browser routing still uses the actual window origin. Compiled hash-route and refresh tests pass with this transformation.

See [verification and limitations](REBUILD_VERIFICATION.md).
