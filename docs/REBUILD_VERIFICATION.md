# Rebuild v2 verification and operating contract

## Scope and evidence

Continuation started on `feat/urban-intelligence-rebuild-v2` at `84cf6a7ca8b427471b8af8b1835677441978ded7`. Audit milestone `7acf0a9` and Pages milestone `84cf6a7` were already pushed. Their previous CI results do not establish final source correctness. No resets, history rewriting, deployments, or hosting changes were performed.

Remaining work hardened session revocation and streaming, provenance and unavailable risk, malformed Groq fallback, bounded webhook ingestion, render-loop allocations, and renderer disposal verification. CI now executes browser tests as well as compatibility, native Pathway, and frontend jobs.

## Authentication and persistence

The frontend requests `session_mode: memory`. The returned opaque token expires after 900 seconds, is held in a module variable, and is never put in local/session storage. Protected API requests and fetch-based SSE carry Authorization. Logout revokes both presented bearer and cookie sessions. Expired/revoked sessions return 401; active SSE rechecks validity and exits on revocation. Polling every eight seconds continues when streaming fails.

Reload loses the in-memory token. The compatibility cookie can restore a session only when browser policy permits it; otherwise sign in again. No refresh-token mechanism is claimed. Production cookies are Secure and HttpOnly. Cookie-authenticated mutations require an allowlisted Origin and X-Requested-With. CORS disallows wildcard configuration. Hosted cross-site authentication remains UNVERIFIED until separately approved backend deployment and browser checks.

SQLite account/session storage is retained. Set AUTH_DB_PATH on an existing persistent disk before production use; ephemeral storage is not persistent. No database migration or Render configuration change is included.

## Data contract

Source evidence includes source_class, status, observed_at, ingested_at, and unavailable_reason. Classes distinguish REAL, SIMULATED, WEBHOOK, DERIVED, and NOT_CONFIGURED. Fresh observations, stale observations, actual connector health, and connectivity checks remain separate. GTFS requires a valid feed URL and decoded protobuf observations; configuration notices cannot refresh transit data. Unimplemented traffic providers stay NOT_CONFIGURED. Freshness defaults to 600 seconds and supports per-source overrides.

No eligible city observations means risk_score null and risk_level UNKNOWN, with a reason. UI shows unavailable, not zero/LOW. Risk is explicitly a rule-based heuristic, not a probability or prediction. History uses recorded timestamp positions and breaks lines across gaps greater than ten minutes. Telemetry/history are in-memory; lists and rolling buffers are bounded.

Groq is optional and backend-only. GROQ_MODEL takes precedence over the legacy LLM_MODEL variable. The documented qwen/qwen3.8-27b is a provider preview model; listing does not prove account availability. Actual authenticated Groq calls remain UNVERIFIED. Missing keys, provider errors, and malformed structured responses use deterministic fallback. Error logs omit exception text that might contain credentials. The previously exposed key must be revoked; never reuse it.

## Local verification, 13 October 2026

- VERIFIED: requirements-dev dependencies installed; backend pytest: 99 passed, 1 skipped (native-only test on Windows), 3 deprecation warnings. A sandbox attempt could not create pytest temporary directories; the authorized rerun with a workspace basetemp passed.
- VERIFIED: non-empty stream regression processed 2 events with native=False (Windows compatibility mode). Final Linux native execution must be checked against the pushed commit in GitHub CI, not inferred from this result.
- VERIFIED: npm ci succeeded, audit reported zero vulnerabilities. TypeScript, lint, 23 preflight tests, production build, and artifact scan passed. Vite warns about the approximately 916 kB uncompressed lazy Three.js scene chunk; no size-performance claim is made.
- VERIFIED: compiled Pages suite: 2 passed. Direct hash routes/reload, correct assets/API origin, station selection and information panel, pan, zoom and reset, nonblank canvas, responsive widths 360/768/1280, repeated disposal.
- VERIFIED: cross-browser suite: 6 passed across Chromium, Firefox, WebKit. Tests clear cookies, use bearer-authenticated state/SSE, revoke on logout, reject replay, and recover with eight-second polling.
- Renderer measurements: three compiled mounts each reported 22 geometries, 0 textures, 22 draw calls; two old renderers reported 0 geometries and 0 textures after unmount. Visibility listeners returned to baseline. Observed headless FPS was 3.7/3.9/3.7. This is not proof of a global absence of memory leaks, and the 30 FPS laptop target is UNVERIFIED.
- VERIFIED: full Chromium suite: 9 passed, including orbit/selection, reduced motion, WebGL fallback, mobile layouts and application routes. Local runtime smoke passed all 13 HTTP checks, 20 city summaries and advancing stream, with deterministic Copilot fallback. Final staged-secret scan and exact-commit CI results are recorded in the completion report and linked CI run. Tests fail rather than skip if required native Pathway falls back.

## Deleted starter files

`frontend/src/App.tsx`, `frontend/src/App.css`, `frontend/src/assets/hero.png`, `frontend/src/assets/react.svg`, and `frontend/src/assets/vite.svg` were unused starter files. Source/build/test/workflow reference searches found only self-references in the starter and historical documentation. The actual main.tsx imports app/App.tsx. Successful production compilation and compiled routes corroborate the deletion. The voxel assets and preview remain intact.

## Approval boundaries

Feature-branch commit/push is authorized. Merge, manual Pages publication, Render deployment/settings changes, and production resources require separate approval. Follow FRONTEND_HOSTING.md for exact dashboard steps. A healthy public endpoint is only a point-in-time observation and does not prove the new source is deployed. Do not call the hosted product production-ready before approved publication and live verification.
