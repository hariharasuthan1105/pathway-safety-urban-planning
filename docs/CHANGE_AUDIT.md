# Source audit

The retained voxel project was integrated into the existing GitHub repository from main commit `9aa3862ab4aaa06a8e5060851f15c0ef244e680b`, on branch `codex/voxel-telemetry-reliability`. Existing remote callback regression tests and history are preserved. This revision fixes telemetry provenance, offline status and production configuration without rebuilding the voxel scene. The revised ZIP is generated from the final Git commit. No Render deployment was performed.

Active entry: `frontend/src/main.tsx` → `frontend/src/app/App.tsx`. The mounted `features/three/CityScene.tsx` was replaced in place on Landing and Login; `/app/digital-twin` reuses it. Nine protected routes now share authentication and telemetry context. Legacy root HTML, old components and Streamlit files are retained but are not the active React entry.

Reviewed backend subscription/connector/anomaly path, API URL handling, shared API client, geographic markers and styles. Native keyword callback and retraction behaviour are covered by regression tests. Missing coordinates remain unlocated.

## Changes from original archive

- Modified: `.env.example`
- Modified: `.gitignore`
- Modified: `render.yaml`
- Added: `requirements-core.txt`
- Added: `requirements-dev.txt`
- Modified: `requirements-render.txt`
- Modified: `requirements.txt`
- Added: `docs/REDESIGN_ARCHITECTURE.md`
- Added: `frontend/.env.production.example`
- Added: `frontend/package-lock.json`
- Added: `frontend/package.json`
- Modified: `frontend/playwright.config.ts`
- Added: `frontend/tsconfig.json`
- Modified: `frontend/vite.config.ts`
- Modified: `src/main.py`
- Modified: `src/pathway_compat.py`
- Modified: `src/webhook_server.py`
- Added: `tests/runtime_smoke.py`
- Added: `tests/stream_regression.py`
- Modified: `tests/test_anomaly_detection.py`
- Modified: `tests/test_data_sources.py`
- Modified: `tests/test_intelligence_engine.py`
- Added: `tests/test_subscription_contract.py`
- Added: `tests/test_truthful_contracts.py`
- Modified: `.github/workflows/ci.yml`
- Modified: `frontend/e2e/auth.spec.ts`
- Added: `frontend/e2e/resilience.spec.ts`
- Added: `frontend/e2e/voxel.spec.ts`
- Added: `frontend/e2e/workstation.spec.ts`
- Modified: `frontend/src/index.css`
- Modified: `frontend/src/app/App.tsx`
- Modified: `frontend/src/context/AuthContext.tsx`
- Added: `frontend/src/context/TelemetryContext.tsx`
- Modified: `frontend/src/layouts/AppShell.tsx`
- Modified: `frontend/src/lib/api.ts`
- Modified: `frontend/src/lib/config.ts`
- Modified: `frontend/src/pages/Cities.tsx`
- Modified: `frontend/src/pages/Copilot.tsx`
- Added: `frontend/src/pages/DigitalTwin.tsx`
- Modified: `frontend/src/pages/Environment.tsx`
- Modified: `frontend/src/pages/Events.tsx`
- Modified: `frontend/src/pages/Landing.tsx`
- Modified: `frontend/src/pages/Login.tsx`
- Modified: `frontend/src/pages/Overview.tsx`
- Modified: `frontend/src/pages/Risk.tsx`
- Modified: `frontend/src/pages/Settings.tsx`
- Modified: `frontend/src/pages/Signup.tsx`
- Modified: `frontend/src/pages/Traffic.tsx`
- Added: `frontend/src/components/ui/Intelligence.tsx`
- Added: `frontend/src/components/ui/Workstation.tsx`
- Modified: `frontend/src/features/copilot/CopilotWorkspace.tsx`
- Modified: `frontend/src/features/map/SouthIndiaMap.tsx`
- Modified: `frontend/src/features/three/CityScene.tsx`
- Added: `frontend/src/features/three/GeographicEvidence.tsx`
- Added: `frontend/src/features/three/voxel.css`
- Added: `frontend/src/features/three/voxelSimulation.ts`
- Added: `frontend/src/features/three/voxelWorld.ts`
- Modified: `src/data_sources/base.py`
- Modified: `src/data_sources/models.py`
- Modified: `src/data_sources/public_safety.py`
- Modified: `src/data_sources/real_sources.py`
- Modified: `src/data_sources/traffic_sim.py`
- Modified: `src/data_sources/urban_planning.py`
- Modified: `src/processing/anomaly_detection.py`
- Modified: `src/processing/city_state.py`
- Modified: `src/processing/copilot_engine.py`
- Modified: `src/processing/llm_provider.py`
- Modified: `src/processing/rag_system.py`
- Modified: `src/processing/zones.py`
