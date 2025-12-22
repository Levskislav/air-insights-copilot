# Project Plan (EN): Agentic “Air & Insights Copilot”

This is a **step-by-step project plan with progress statuses** for the “Air & Insights Copilot” agent.

## Project goal
Build an **agentic assistant** that:
- fetches **weather + air quality** from **Open-Meteo** (no key),
- optionally fetches **NASA APOD**,
- calls **GitHub Models (free inference)** to synthesize actionable guidance,
- exposes a **REST API + OpenAPI 3.0** suitable for Copilot Studio Tool/Action or a free UI.

---

## 0) Status legend
- ⬜ Not Started
- 🟨 In Progress
- 🟥 Blocked
- 🟩 Done

---

## 1) Prerequisites (to start)

### 1.1 Local environment
- Python 3.10+ (recommended 3.11)
- git
- Terminal
- Optional: Docker

### 1.2 Access/keys
- GitHub PAT for GitHub Models inference
- Optional: NASA_API_KEY or DEMO_KEY

### 1.3 Minimal decisions
- Track choice:
  - Start with **Track B (recommended)**: FastAPI + web/CLI UI
  - Then Track A: Copilot Studio integration
- Guidance language: EN or BG

### 1.4 Definition of Done (minimum)
- `POST /analyze` input: `{ latitude, longitude, hours }` → output: `{ pm25_avg, pm10_avg, temp_avg, guidance_text }`
- Optional: `GET /apod/today` → `{ title, url, explanation }`
- Agentic flow: plan → fetch → validate → cache (10 min) → reason (LLM) → respond
- Retry/backoff + timeouts
- Tests: unit + minimal integration (stub external calls)
- Logging: request + error traces
- Attribution: “Weather data by Open-Meteo.com”

---

## 2) Step-by-step plan

Below is the same plan as an ordered list of concrete steps.  
Each step shows: **What**, **Why**, **Depends on**, **Output**, **Status**, and **Done when…**.

1. **Kickoff: confirm scope, Track, DoD**  
   - **What**: Align on overall scope, choose Track(s), define Definition of Done.  
   - **Why**: Everyone agrees what "done" means and what will be delivered.  
   - **Depends on**: —  
   - **Output**: `docs/scope.md` with scope + DoD.  
   - **Status**: 🟩 Done  
   - **Done when**: Scope and success criteria are written down and agreed.

2. **Create repo and folders (`service/`, `agent/`, `tests/`, `docs/`, `ui/`)**  
   - **What**: Initialize git repo and create the folder skeleton.  
   - **Why**: Clear structure → easier navigation and maintainability.  
   - **Depends on**: Step 1  
   - **Output**: Repo skeleton committed.  
   - **Status**: 🟩 Done  
   - **Done when**: All folders exist and are checked in.

3. **Set up dev environment, dependencies, and `.env` layer**  
   - **What**: Add `requirements.txt`, create virtualenv, `.env.example`, and basic config.  
   - **Why**: Everyone can install and run the project the same way.  
   - **Depends on**: Step 2  
   - **Output**: `requirements.txt`, `.env.example`, working local run.  
   - **Status**: 🟩 Done  
   - **Done when**: New dev can clone, install, and start the app without errors.

4. **Define API schemas (Pydantic models)**  
   - **What**: Implement request/response models in `service/schemas.py`.  
   - **Why**: Strong validation and automatic OpenAPI generation.  
   - **Depends on**: Step 3  
   - **Output**: `service/schemas.py` with `AnalyzeRequest`, `AnalyzeResponse`, `ApodResponse`.  
   - **Status**: 🟩 Done  
   - **Done when**: Models match the spec and show correctly in Swagger.

5. **Implement service endpoints: `/analyze` (+ optional `/apod/today`)**  
   - **What**: Add FastAPI routes in `service/routes.py` and wire them to the agent.  
   - **Why**: Expose the core functionality over HTTP.  
   - **Depends on**: Step 4  
   - **Output**: `service/routes.py` with working endpoints.  
   - **Status**: 🟩 Done  
   - **Done when**: Swagger UI shows both endpoints and they return stub/real responses.

6. **Build Open-Meteo tools (air quality + weather)**  
   - **What**: Implement `fetch_air_quality` and `fetch_weather` in `agent/tools/open_meteo.py`.  
   - **Why**: Get free weather and air quality data with no API key.  
   - **Depends on**: Step 3  
   - **Output**: `agent/tools/open_meteo.py` returning real JSON from Open-Meteo.  
   - **Status**: 🟩 Done  
   - **Done when**: Manual calls return the expected JSON payloads.

7. **Add retry/backoff helper for HTTP calls**  
   - **What**: Implement `request_with_retry` in `agent/retry.py`.  
   - **Why**: Make external calls resilient to 429/5xx and network hiccups.  
   - **Depends on**: Step 3  
   - **Output**: `agent/retry.py` used by all HTTP tools.  
   - **Status**: 🟩 Done  
   - **Done when**: Retries on retryable errors and respects timeouts.

8. **Validation of inputs and payloads**  
   - **What**: Implement `validate_lat_lon` and `validate_open_meteo_payload` in `agent/validate.py`.  
   - **Why**: Enforce quality gates and detect sparse/missing data.  
   - **Depends on**: Steps 4–7  
   - **Output**: `agent/validate.py` with `DataQualityFlags` and validation helpers.  
   - **Status**: 🟩 Done  
   - **Done when**: Invalid lat/lon are rejected and bad payloads are flagged correctly.

9. **Compute safe averages**  
   - **What**: Implement `safe_avg` in `agent/compute.py`.  
   - **Why**: Correct statistics even when some values are missing.  
   - **Depends on**: Step 8  
   - **Output**: `agent/compute.py`.  
   - **Status**: 🟩 Done  
   - **Done when**: Averages ignore `None` and return `None` when no valid data exists.

10. **Implement cache with 10‑minute TTL**  
    - **What**: Add in-memory TTL cache in `agent/cache.py` keyed by `<lat, lon, hours>`.  
    - **Why**: Reduce external calls and improve response times.  
    - **Depends on**: Step 3  
    - **Output**: `agent/cache.py` with `cache_key`, `ttl_cache_get`, `ttl_cache_set`.  
    - **Status**: 🟩 Done  
    - **Done when**: Cache hits and misses are observable in logs.

11. **Minimal planner**  
    - **What**: Implement `plan_for_analyze` in `agent/planner.py`.  
    - **Why**: Give the system an "agent feel" and explicit tool selection.  
    - **Depends on**: Step 8  
    - **Output**: `agent/planner.py` returning which tools/variables to use.  
    - **Status**: 🟩 Done  
    - **Done when**: Planner returns a consistent plan for `/analyze`.

12. **GitHub Models LLM tool**  
    - **What**: Implement `generate_guidance_text` in `agent/tools/github_models_llm.py`.  
    - **Why**: Turn numeric data into human-friendly guidance with fallback.  
    - **Depends on**: Step 3  
    - **Output**: `agent/tools/github_models_llm.py`.  
    - **Status**: 🟩 Done  
    - **Done when**: Returns guidance text and falls back gracefully if LLM fails.

13. **Prompt library for the LLM**  
    - **What**: Create `guidance_system.txt` and `guidance_user_template.txt` in `agent/prompts/`.  
    - **Why**: Ensure consistent, safe, and concise responses.  
    - **Depends on**: Step 12  
    - **Output**: `agent/prompts/*` files.  
    - **Status**: 🟩 Done  
    - **Done when**: Generated guidance is actionable, 3–6 sentences, with uncertainty notes when needed.

14. **Agent orchestrator (plan → fetch → validate → cache → LLM)**  
    - **What**: Implement `analyze_air_and_weather` in `agent/orchestrator.py`.  
    - **Why**: Central agentic flow coordinating all tools and logic.  
    - **Depends on**: Steps 6–13  
    - **Output**: `agent/orchestrator.py`.  
    - **Status**: 🟩 Done  
    - **Done when**: `/analyze` works end-to-end with real data and LLM guidance.

15. **Attribution enforcement**  
    - **What**: Always append "Weather data by Open-Meteo.com" to guidance.  
    - **Why**: Fulfills the attribution requirement.  
    - **Depends on**: Step 14  
    - **Output**: Global rule in orchestrator or response builder.  
    - **Status**: 🟩 Done  
    - **Done when**: Every `/analyze` response includes the attribution string.

16. **Web UI or CLI (Track B demo)**  
    - **What**: Add a minimal UI in `ui/` or a CLI that calls `/analyze`.  
    - **Why**: Provide a human-friendly way to demo the system.  
    - **Depends on**: Step 14  
    - **Output**: `ui/web/*` or CLI script.  
    - **Status**: ⏭️ Skipped (using Track A: Copilot Studio instead)  
    - **Done when**: A user can input coords/hours and see averages + guidance.

17. **Unit tests**  
    - **What**: Write tests for validation and compute logic in `tests/`.  
    - **Why**: Protect core logic from regressions.  
    - **Depends on**: Steps 8–9  
    - **Output**: `tests/test_validate.py`, `tests/test_compute.py`, etc.  
    - **Status**: ⬜ Not Started  
    - **Done when**: `pytest` passes locally.

18. **Integration test with stubbed tools**  
    - **What**: Add `tests/test_integration_analyze.py` that stubs external tools.  
    - **Why**: CI‑safe test that doesn’t depend on real APIs.  
    - **Depends on**: Step 14  
    - **Output**: `tests/test_integration_analyze.py`.  
    - **Status**: ⬜ Not Started  
    - **Done when**: Test passes without making real HTTP calls.

19. **Logging and observability**  
    - **What**: Add structured logs with `request_id`, cache events, latencies, and errors.  
    - **Why**: Easier debugging and production readiness.  
    - **Depends on**: Step 14  
    - **Output**: Logging configuration and calls inside `service/` and `agent/`.  
    - **Status**: ⬜ Not Started  
    - **Done when**: Logs show full trace for each request.

20. **Performance check (cached p95 < 2s)**  
    - **What**: Run a simple benchmark focusing on cached responses.  
    - **Why**: Confirm performance requirement is met.  
    - **Depends on**: Steps 10 and 14  
    - **Output**: Short note or script with results.  
    - **Status**: ⬜ Not Started  
    - **Done when**: Cached p95 latency is under 2 seconds.

21. **Export OpenAPI 3.0 file**  
    - **What**: Save `service/openapi.json` from the running FastAPI app.  
    - **Why**: Required for Copilot Studio Tool import.  
    - **Depends on**: Step 5  
    - **Output**: `service/openapi.json` committed (if desired).  
    - **Status**: ⬜ Not Started  
    - **Done when**: File is generated and validated by Swagger/Copilot.

22. **Docs: README + runbook**  
    - **What**: Write `docs/README.md` (or root `README.md`) and a brief runbook.  
    - **Why**: Make the project easy to understand and run.  
    - **Depends on**: Steps 16–21  
    - **Output**: `docs/README.md`, optionally `docs/runbook.md`.  
    - **Status**: ⬜ Not Started  
    - **Done when**: A new user can follow docs to run everything locally.

23. **Copilot tool snippet (Track A)**  
    - **What**: Prepare a copy‑paste snippet for Copilot Studio Tool configuration.  
    - **Why**: Speed up Track A integration.  
    - **Depends on**: Step 21  
    - **Output**: `docs/copilot_tool_snippet.md`.  
    - **Status**: ⬜ Not Started  
    - **Done when**: Snippet can be used directly in Copilot Studio.

24. **Screenshots for Track B UI/CLI**  
    - **What**: Capture 2–3 screenshots (or a short video) of the working demo.  
    - **Why**: Visual proof and documentation of behavior.  
    - **Depends on**: Step 16  
    - **Output**: `screenshots/` folder (or media link).  
    - **Status**: ⬜ Not Started  
    - **Done when**: Screenshots show input + response clearly.

25. **Track A: import OpenAPI and configure orchestration**  
    - **What**: Import `openapi.json` in Copilot Studio and configure the Tool.  
    - **Why**: Enable the assistant to call the API as a Tool.  
    - **Depends on**: Step 21 + Copilot access  
    - **Output**: Copilot Tool configuration.  
    - **Status**: ⬜ Not Started  
    - **Done when**: Chat in Copilot successfully invokes the Tool.

26. **Final review and release**  
    - **What**: Verify all deliverables, clean up, and tag a release.  
    - **Why**: Ensure a polished, complete handoff.  
    - **Depends on**: All previous steps  
    - **Output**: Release artifact or tag, plus final checklist.  
    - **Status**: ⬜ Not Started  
    - **Done when**: All deliverables are present and validated.

---

## 2.1) Bonus: NASA APOD Tool
- **What**: Implemented `GET /apod/today` endpoint with `agent/tools/nasa_apod.py`
- **Status**: 🟩 Done
- **Output**: Returns `{ title, url, explanation }` from NASA APOD API

---

## 3) Fast MVP path
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 22 → 24 → 21

---
