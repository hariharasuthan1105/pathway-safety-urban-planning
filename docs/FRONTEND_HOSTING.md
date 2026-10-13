# Why the published frontend was old

Verified on 13 October 2026 using the GitHub Pages API, workflow records, served HTML and local process command line:

- GitHub `main` is `5857851c24474d8a5bdf90fc4b8434c3f14dc818`, a squash merge of the voxel changes. Its tree matches the previously verified voxel revision. A squash merge does not preserve the original commit as an ancestor.
- Public site: https://hariharasuthan1105.github.io/pathway-safety-urban-planning/
- Host: GitHub Pages. Current publishing source: `main`, repository root `/`, legacy branch publishing.
- That source publishes root `index.html`, `style.css` and `script.js`. It loads Three.js r128 and contains “Grounded RAG + OpenAI” plus `http://localhost:8000/api/state`.
- CI builds `frontend/dist` but previously uploaded no Pages artifact. A successful Pages root deployment therefore still published the legacy frontend.
- The current local tab at http://127.0.0.1:5173/ serves `work/github-revision/frontend` through Vite. Its actual DOM contains `METROPOLIS / VOXEL WORLD`, the railway station/airport/bus interchange selection and camera controls. Its environment uses the verified local backend at `http://127.0.0.1:10000`.

## Active React entry

`frontend/index.html` → `frontend/src/main.tsx` → `frontend/src/app/App.tsx` → route component.

`/` and `/login` import `frontend/src/features/three/CityScene.tsx`. The protected `/app/digital-twin` workspace imports the same component. It imports the existing voxel geometry and simulation; this fix does not recreate the scene. Root HTML and the unused `frontend/src/App.tsx` are separate legacy entries.

## Required owner-approved publishing steps

These steps have **not** been applied. They use GitHub Pages, not the unverified Render frontend Blueprint.

1. Restore or choose the actual backend service and confirm its HTTPS `/api/health` returns HTTP 200 with `status: HEALTHY`. The previously used `https://urban-intelligence-backend-z869.onrender.com/api/health` currently returns **503**, with response text “This service has been suspended by its owner.” Authenticated Render logs are unavailable; the underlying reason is not established.
2. Set that backend's `CORS_ORIGINS` to `https://hariharasuthan1105.github.io` (an origin has no repository path). Review secure cross-site session-cookie configuration. Actual hosted authentication remains unverified.
3. Review and merge the `fix/pages-voxel-build` source changes into `main`. Do not publish the root legacy files as the new React application.
4. In repository **Settings → Secrets and variables → Actions → Variables → New repository variable**, set `VITE_API_BASE_URL` to the verified HTTPS backend origin. It is a public build variable, not an API key. Do not put Groq credentials in Vite variables. No healthy public origin has been selected during this investigation.
5. In repository **Settings → Pages → Build and deployment → Source**, select **GitHub Actions**. The intended repository is `hariharasuthan1105/pathway-safety-urban-planning`, branch `main`.
6. After deployment approval, open **Actions → Publish voxel frontend to GitHub Pages → Run workflow**, select branch **main**, and run it. Publication is manual; pushing the fix branch does not run this deployment workflow.
7. The workflow checks backend health, runs `npm ci && npm run build` with working directory `frontend`, uploads **`frontend/dist`**, then publishes that artifact. It embeds `VITE_API_BASE_URL`, `VITE_BASE_PATH=/pathway-safety-urban-planning/` and `VITE_ROUTER_MODE=hash` at build time.
8. Verify the published page loads hashed Vite assets under `/pathway-safety-urban-planning/assets/`, displays `METROPOLIS / VOXEL WORLD`, and makes API requests to the configured public backend. Check signup/login and camera controls. Pages routes use `/#/login` and `/#/app/digital-twin`, so reloading protected URLs works without server rewrites.

The existing root legacy application is retained for source history and working legacy features. The Pages artifact contains only compiled React assets, so those old files and branding are not published by the new workflow. [GitHub's custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) describes this artifact-based publishing mechanism.

## Local run

Project directory on this machine:

`C:\Users\hariharasuthan\Documents\Codex\2026-10-12\files-mentioned-by-the-user-pathway\work\github-revision`

The reviewed fix branch is `fix/pages-voxel-build`, based on merged `main`. After merging the fix, use an up-to-date clean `main`. Preserve local changes before switching branches or pulling. Run the backend separately with its existing authentication database configuration; local verification uses port 10000. Start that local backend with `CORS_ORIGINS=http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:5173` before testing the preview on port 5174; otherwise cross-origin signup is rejected. Keep the existing `AUTH_DB_PATH` to preserve accounts.

```powershell
cd C:\Users\hariharasuthan\Documents\Codex\2026-10-12\files-mentioned-by-the-user-pathway\work\github-revision\frontend
# Stop this checkout's running Vite process before npm ci on Windows.
npm ci
$env:VITE_API_BASE_URL='http://127.0.0.1:10000'
npm run dev -- --port 5173 --strictPort
```

For a local production build: `npm run build`, then `npm run preview -- --host 127.0.0.1`. These local validation origins are not public deployment configuration.

For Pages-layout validation against the local backend:

```powershell
$env:VITE_API_BASE_URL='http://127.0.0.1:10000'
$env:VITE_BASE_PATH='/pathway-safety-urban-planning/'
$env:VITE_ROUTER_MODE='hash'
# Leave VITE_DEPLOY_TARGET unset for local validation; real Pages builds forbid loopback.
npm run build
npm run preview -- --host 127.0.0.1 --port 5174 --strictPort
```

Open `http://127.0.0.1:5174/pathway-safety-urban-planning/`. In another frontend terminal run `npx playwright test --config playwright.pages.config.ts`. Existing application tests use `npm run test:e2e` against port 5173. `PLAYWRIGHT_EXECUTABLE_PATH` may select an existing Chromium installation.

## Verification of this fix

- `npm ci`: passed after stopping the existing Vite process that held a Windows native CSS module open; 155 packages installed, zero reported audit vulnerabilities. No network installation blocker.
- `npx tsc --noEmit`: passed.
- Root production build with the verified local API origin: passed.
- Pages-subpath production build with hash routes and the same local validation origin: passed. This is a local artifact, not a production deployment using a healthy public API.
- Existing Chromium suite: **8 passed** (camera, station focus, pause/day/night/detail controls, geographic selection, mobile/reduced motion, authentication and workspace routes).
- Compiled Pages-artifact Chromium regression: **1 passed** (voxel rendering, signup, authenticated navigation, protected-route reload, subpath assets and correct local API requests). Its first run was blocked by missing port-5174 CORS configuration on the local backend; rerunning with that explicit test origin passed.
- Missing build origin and localhost Pages target: both correctly rejected.
- Deployment preflight against the known Render service: correctly failed on actual HTTP 503.
- Vite retains a ~915 KB Three.js chunk size warning; no scene redesign was performed.
- Live public site still serves the legacy root artifact until the owner-approved publishing steps are completed. No healthy public backend origin, hosted authentication, or Pages publication of this fix has been verified.

## Pages preflight variable correction

The failed run [38343494503](https://github.com/hariharasuthan1105/pathway-safety-urban-planning/actions/runs/38343494503) received an empty `VITE_API_BASE_URL`. The repository had no Actions repository variables; `new URL('')` produced the unhelpful `Invalid URL` error.

Both verification and Vite build steps now explicitly map `VITE_API_BASE_URL: ${{ vars.VITE_API_BASE_URL }}`. Validation identifies **Settings → Secrets and variables → Actions → Variables → VITE_API_BASE_URL** when the value is missing, malformed or unsuitable. An Actions secret alone does not populate `vars.VITE_API_BASE_URL`.

Set that repository variable to the user-supplied origin `https://urban-intelligence-backend-z869.onrender.com`. The actual health check now returns HTTP 200 with `status: HEALTHY`; this supersedes the earlier suspended-service observation in this document. Render settings were not changed.

Verification: 20 preflight tests passed, 8 browser tests passed, TypeScript passed, and the Pages production build passed using that HTTPS origin. Bundle inspection found the supplied origin and no `http://localhost:8000`; the existing Three.js chunk warning remains. The workflow stays manual and the health check remains required. Review/merge the separate fix branch before an approved manual publication; this correction itself performs neither action.

## Rebuild v2 publishing policy

The feature branch adds main-only path-filtered publication and keeps manual dispatch. No feature branch push deploys. Validation rejects a trailing slash, retries health four times with a 75-second timeout budget, and asserts compiled assets. Prior observations above are historical. The latest preflight timed out on all attempts; health is not verified by a successful build.

Action majors were queried through GitHub releases: checkout/setup-node v7, upload-pages-artifact/deploy-pages v5, configure-pages v6. React Router has two inert loopback URL parser defaults. A scoped build transform replaces those vendor defaults with https://router.invalid; runtime navigation still uses window.location. No API target is substituted. Artifact and route tests cover the compiled build.
