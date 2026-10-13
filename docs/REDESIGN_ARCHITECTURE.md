# Architecture inspection

The active entry is frontend/src/main.tsx → app/App.tsx, using BrowserRouter and cookie authentication. The root src/App.tsx and root HTML/JS are legacy surfaces, not the React entry. Eight protected pages live beneath AppShell. The ZIP omitted package.json, a lockfile and tsconfig; build metadata is restored explicitly.

FastAPI runs in a daemon thread launched by src/main.py. DataSourceManager constructs ConnectorSubject streams; concatenation and the anomaly UDF feed a subscription which updates the shared CityStateManager and RAGSystem. Native Pathway blocks in pw.run(); sinks must be registered first. Windows uses the existing compatibility engine and cannot establish native Linux engine correctness.

API contracts: /api/auth/{signup,login,logout,me}; /api/state; /api/health; /api/cities/{city_id}/history; /api/ask; /events. State originally lacked the frontend's region envelope, fabricated source health, and returned synthetic history. These require additive corrections while retaining legacy fields. Event metadata can appear inside data; adapt at the shared frontend boundary. Groq remains server-side with deterministic fallback.

Implementation direction: one authenticated telemetry provider owns polling and city/event selection. Geographic markers use backend coordinates; the procedural city is explicitly illustrative. Noir tokens and reusable workstation components provide consistent styling across every route. No hosted Site, Git commit or deployment is requested.

## Completed voxel integration

`CityScene.tsx` now mounts the instanced model from `voxelWorld.ts` and transport/crowd simulation from `voxelSimulation.ts`. It remains mounted on the landing and login pages. `DigitalTwin.tsx` adds a ninth protected route, shares telemetry selection and preserves the existing map and inspectors. `GeographicEvidence.tsx` displays source coordinates independently of invented asset geometry. The production build checks the explicit API origin. See README for final verification and unresolved native/Render limitations.

Rebuild v2: unused `frontend/src/App.tsx`, `App.css`, and its three starter assets were removed after reference checks. The active entry remains `frontend/src/app/App.tsx`. Historical legacy-file descriptions above refer to earlier snapshots.
