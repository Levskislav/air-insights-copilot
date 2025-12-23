# Project Plan (EN): OutdoorMate — Complete Outdoor Activity Assistant

This is a **complete step-by-step project plan** for the "OutdoorMate" agent.

---

## Project Vision

**OutdoorMate** is an intelligent assistant that helps users make informed decisions about outdoor activities by providing:
- 🌡️ **Weather data** (temperature, conditions)
- 🌫️ **Air quality** (PM2.5, PM10)
- 🌨️ **Snow conditions** (snowfall, snow depth)
- 📍 **Location search** (place names → coordinates)
- 🚗 **Route weather** (weather along driving routes A → B)
- 🤖 **AI guidance** (personalized recommendations via LLM)

**Integration**: Microsoft Copilot Studio (Track A)

---

## Status Legend
- ⬜ Not Started
- 🟨 In Progress
- 🟥 Blocked
- 🟩 Done

---

## Prerequisites

### Required Access/Keys
| Key | Source | Status |
|-----|--------|--------|
| GitHub PAT | github.com/settings/tokens | 🟩 Done |
| NASA API Key | api.nasa.gov | 🟩 Done (optional) |
| Google Maps API Key | console.cloud.google.com | ⬜ Needed for Steps 27-29 |

### Development Environment
- Python 3.10+ (recommended 3.11)
- Git
- GitHub Codespaces (for public API hosting)
- Microsoft Copilot Studio access

---

## Part 1: Foundation (Steps 1-3)

1. **Project Kickoff**
   - **What**: Define scope, choose Track A, set Definition of Done.
   - **Why**: Everyone agrees what "done" means and what will be delivered.
   - **Depends on**: —
   - **Output**: `docs/scope.md` with scope + DoD.
   - **Status**: 🟩 Done
   - **Done when**: Scope and success criteria are written down and agreed.

2. **Repository Structure**
   - **What**: Initialize git repo and create folder skeleton.
   - **Why**: Clear structure → easier navigation and maintainability.
   - **Depends on**: Step 1
   - **Output**: Folders: `service/`, `agent/`, `tests/`, `docs/`
   - **Status**: 🟩 Done
   - **Done when**: All folders exist and are checked in.

3. **Dev Environment**
   - **What**: Add `requirements.txt`, create virtualenv, `.env.example`, and basic config.
   - **Why**: Everyone can install and run the project the same way.
   - **Depends on**: Step 2
   - **Output**: `requirements.txt`, `.env.example`, working local run.
   - **Status**: 🟩 Done
   - **Done when**: New dev can clone, install, and start the app without errors.

---

## Part 2: Core API (Steps 4-15)

4. **API Schemas**
   - **What**: Implement request/response models in `service/schemas.py`.
   - **Why**: Strong validation and automatic OpenAPI generation.
   - **Depends on**: Step 3
   - **Output**: `service/schemas.py` with `AnalyzeRequest`, `AnalyzeResponse`, `ApodResponse`.
   - **Status**: 🟩 Done
   - **Done when**: Models match the spec and show correctly in Swagger.

5. **FastAPI Endpoints**
   - **What**: Add FastAPI routes in `service/routes.py` and wire them to the agent.
   - **Why**: Expose the core functionality over HTTP.
   - **Depends on**: Step 4
   - **Output**: `service/routes.py` with `/analyze`, `/apod/today`, health check.
   - **Status**: 🟩 Done
   - **Done when**: Swagger UI shows all endpoints and they return responses.

6. **Open-Meteo Tools**
   - **What**: Implement `fetch_air_quality` and `fetch_weather` in `agent/tools/open_meteo.py`.
   - **Why**: Get free weather and air quality data with no API key.
   - **Depends on**: Step 3
   - **Output**: `agent/tools/open_meteo.py` returning real JSON from Open-Meteo.
   - **Status**: 🟩 Done
   - **Done when**: Manual calls return the expected JSON payloads.

7. **Retry/Backoff Helper**
   - **What**: Implement `request_with_retry` in `agent/retry.py`.
   - **Why**: Make external calls resilient to 429/5xx and network hiccups.
   - **Depends on**: Step 3
   - **Output**: `agent/retry.py` used by all HTTP tools.
   - **Status**: 🟩 Done
   - **Done when**: Retries on retryable errors and respects timeouts.

8. **Input Validation**
   - **What**: Implement `validate_lat_lon` and `validate_open_meteo_payload` in `agent/validate.py`.
   - **Why**: Enforce quality gates and detect sparse/missing data.
   - **Depends on**: Steps 4–7
   - **Output**: `agent/validate.py` with `DataQualityFlags` and validation helpers.
   - **Status**: 🟩 Done
   - **Done when**: Invalid lat/lon are rejected and bad payloads are flagged correctly.

9. **Safe Averages**
   - **What**: Implement `safe_avg` in `agent/compute.py`.
   - **Why**: Correct statistics even when some values are missing.
   - **Depends on**: Step 8
   - **Output**: `agent/compute.py`.
   - **Status**: 🟩 Done
   - **Done when**: Averages ignore `None` and return `None` when no valid data exists.

10. **TTL Cache**
    - **What**: Add in-memory TTL cache in `agent/cache.py` keyed by `<lat, lon, hours>`.
    - **Why**: Reduce external calls and improve response times.
    - **Depends on**: Step 3
    - **Output**: `agent/cache.py` with `cache_key`, `cache_get`, `cache_set`.
    - **Status**: 🟩 Done
    - **Done when**: Cache hits and misses are observable in logs.

11. **Planner**
    - **What**: Implement `plan_for_analyze` in `agent/planner.py`.
    - **Why**: Give the system an "agent feel" and explicit tool selection.
    - **Depends on**: Step 8
    - **Output**: `agent/planner.py` returning which tools/variables to use.
    - **Status**: 🟩 Done
    - **Done when**: Planner returns a consistent plan for `/analyze`.

12. **LLM Tool**
    - **What**: Implement `generate_guidance_text` in `agent/tools/github_models_llm.py`.
    - **Why**: Turn numeric data into human-friendly guidance with fallback.
    - **Depends on**: Step 3
    - **Output**: `agent/tools/github_models_llm.py`.
    - **Status**: 🟩 Done
    - **Done when**: Returns guidance text and falls back gracefully if LLM fails.

13. **Prompt Library**
    - **What**: Create `guidance_system.txt` and `guidance_user_template.txt` in `agent/prompts/`.
    - **Why**: Ensure consistent, safe, and concise responses.
    - **Depends on**: Step 12
    - **Output**: `agent/prompts/*` files.
    - **Status**: 🟩 Done
    - **Done when**: Generated guidance is actionable, 3–6 sentences, with uncertainty notes.

14. **Orchestrator**
    - **What**: Implement `analyze_air_and_weather` in `agent/orchestrator.py`.
    - **Why**: Central agentic flow coordinating all tools and logic.
    - **Depends on**: Steps 6–13
    - **Output**: `agent/orchestrator.py`.
    - **Status**: 🟩 Done
    - **Done when**: `/analyze` works end-to-end with real data and LLM guidance.

15. **Attribution**
    - **What**: Always append "Weather data by Open-Meteo.com" to guidance.
    - **Why**: Fulfills the attribution requirement.
    - **Depends on**: Step 14
    - **Output**: Global rule in orchestrator or response builder.
    - **Status**: 🟩 Done
    - **Done when**: Every `/analyze` response includes the attribution string.

---

## Part 3: Deployment & Integration (Steps 16-26)

16. **Web UI**
    - **What**: Add a minimal UI in `ui/` or a CLI that calls `/analyze`.
    - **Why**: Provide a human-friendly way to demo the system.
    - **Depends on**: Step 14
    - **Output**: `ui/web/*` or CLI script.
    - **Status**: ⏭️ Skipped (using Track A: Copilot Studio instead)
    - **Done when**: A user can input coords/hours and see averages + guidance.

17. **Unit Tests**
    - **What**: Write tests for validation and compute logic in `tests/`.
    - **Why**: Protect core logic from regressions.
    - **Depends on**: Steps 8–9
    - **Output**: `tests/test_validate.py`, `tests/test_compute.py`, etc.
    - **Status**: ⬜ Not Started
    - **Done when**: `pytest` passes locally.

18. **Integration Tests**
    - **What**: Add `tests/test_integration_analyze.py` that stubs external tools.
    - **Why**: CI‑safe test that doesn't depend on real APIs.
    - **Depends on**: Step 14
    - **Output**: `tests/test_integration_analyze.py`.
    - **Status**: ⬜ Not Started
    - **Done when**: Test passes without making real HTTP calls.

19. **Logging**
    - **What**: Add structured logs with `request_id`, cache events, latencies, and errors.
    - **Why**: Easier debugging and production readiness.
    - **Depends on**: Step 14
    - **Output**: Logging configuration and calls inside `service/` and `agent/`.
    - **Status**: ⬜ Not Started
    - **Done when**: Logs show full trace for each request.

20. **Performance Check**
    - **What**: Run a simple benchmark focusing on cached responses.
    - **Why**: Confirm performance requirement is met.
    - **Depends on**: Steps 10 and 14
    - **Output**: Short note or script with results.
    - **Status**: ⬜ Not Started
    - **Done when**: Cached p95 latency is under 2 seconds.

21. **Export OpenAPI**
    - **What**: Save `service/openapi.json` from the running FastAPI app.
    - **Why**: Required for Copilot Studio Tool import.
    - **Depends on**: Step 5
    - **Output**: `service/openapi.json` committed.
    - **Status**: 🟩 Done
    - **Done when**: File is generated and validated by Swagger/Copilot.

22. **Documentation**
    - **What**: Write `docs/README.md` (or root `README.md`) and a brief runbook.
    - **Why**: Make the project easy to understand and run.
    - **Depends on**: Steps 16–21
    - **Output**: `docs/README.md`, optionally `docs/runbook.md`.
    - **Status**: ⬜ Not Started
    - **Done when**: A new user can follow docs to run everything locally.

23. **Copilot Tool Snippet**
    - **What**: Prepare a copy‑paste snippet for Copilot Studio Tool configuration.
    - **Why**: Speed up Track A integration.
    - **Depends on**: Step 21
    - **Output**: `docs/copilot_tool_snippet.md`.
    - **Status**: 🟩 Done
    - **Done when**: Snippet can be used directly in Copilot Studio.

24. **Screenshots**
    - **What**: Capture 2–3 screenshots (or a short video) of the working demo.
    - **Why**: Visual proof and documentation of behavior.
    - **Depends on**: Step 25
    - **Output**: `screenshots/` folder (or media link).
    - **Status**: ⬜ Not Started
    - **Done when**: Screenshots show input + response clearly.

25. **Copilot Studio Integration**
    - **What**: Import `openapi.json` in Copilot Studio and configure the Tool.
    - **Why**: Enable the assistant to call the API as a Tool.
    - **Depends on**: Step 21 + Copilot access
    - **Output**: Copilot Tool configuration.
    - **Status**: 🟩 Done
    - **Done when**: Chat in Copilot successfully invokes the Tool.

26. **GitHub Codespaces Deployment**
    - **What**: Configure `.devcontainer/devcontainer.json` for cloud deployment.
    - **Why**: Provide public HTTPS URL for Copilot Studio.
    - **Depends on**: Step 3
    - **Output**: Working Codespace with public port 8000.
    - **Status**: 🟩 Done
    - **Done when**: API is accessible via public URL.

---

## Part 4: Snow Data (Steps 27-28) 🌨️

27. **Snow Tool**
    - **What**: Add `fetch_snow` function to `agent/tools/open_meteo.py`.
    - **Why**: Track snowfall and snow depth for winter activities.
    - **Depends on**: Step 6
    - **API**: Open-Meteo (free, no key needed)
    - **Output**: `fetch_snow(lat, lon, hours)` returning `snowfall`, `snow_depth` arrays.
    - **Status**: ⬜ Not Started
    - **Done when**: API returns snow data correctly.

28. **Update /analyze for Snow**
    - **What**: Add `snowfall_sum`, `snow_depth_avg` to `AnalyzeResponse` and update orchestrator.
    - **Why**: Include snow data in analysis and LLM guidance.
    - **Depends on**: Step 27
    - **Output**: Updated `service/schemas.py`, `agent/orchestrator.py`, `agent/prompts/`.
    - **Status**: ⬜ Not Started
    - **Done when**: `/analyze` returns snow data with updated guidance.

---

## Part 5: Geocoding (Steps 29-31) 📍

29. **Google Maps Setup**
    - **What**: Enable Geocoding API in Google Cloud Console and get API key.
    - **Why**: Required for converting place names to coordinates.
    - **Depends on**: —
    - **Output**: `GOOGLE_MAPS_API_KEY` in `.env`.
    - **Status**: ⬜ Not Started
    - **Done when**: API key works in test request.

30. **Geocoding Tool**
    - **What**: Implement `geocode_place` in `agent/tools/google_geocoding.py`.
    - **Why**: Convert "София" → `{ lat: 42.6977, lon: 23.3219 }`.
    - **Depends on**: Step 29
    - **Output**: `agent/tools/google_geocoding.py`.
    - **Status**: ⬜ Not Started
    - **Done when**: `geocode_place("Sofia")` returns correct coordinates.

31. **New /geocode Endpoint**
    - **What**: Add `POST /geocode` endpoint in `service/routes.py`.
    - **Why**: Allow direct geocoding requests from users/Copilot.
    - **Depends on**: Step 30
    - **Output**: `GeocodeRequest`, `GeocodeResponse` schemas + route.
    - **Status**: ⬜ Not Started
    - **Done when**: Swagger shows `/geocode` and it works.

---

## Part 6: Enhanced Analyze (Steps 32-33) 📍

32. **Update AnalyzeRequest Schema**
    - **What**: Add optional `place_name` field alongside coordinates.
    - **Why**: User can provide either coordinates OR place name.
    - **Depends on**: Step 31
    - **Output**: Updated `AnalyzeRequest` with validation.
    - **Status**: ⬜ Not Started
    - **Done when**: Request accepts `{ place_name: "Витоша", hours: 6 }`.

33. **Auto-Geocode in Orchestrator**
    - **What**: If `place_name` provided, geocode before fetching weather.
    - **Why**: Seamless experience for users who don't know coordinates.
    - **Depends on**: Steps 30, 32
    - **Output**: Updated `agent/orchestrator.py`.
    - **Status**: ⬜ Not Started
    - **Done when**: `/analyze` works with place name input.

---

## Part 7: Route Weather (Steps 34-37) 🚗

34. **Google Directions Setup**
    - **What**: Enable Directions API in Google Cloud Console.
    - **Why**: Required for getting route waypoints.
    - **Depends on**: Step 29
    - **Output**: Same API key works for Directions.
    - **Status**: ⬜ Not Started
    - **Done when**: Directions API test request succeeds.

35. **Directions Tool**
    - **What**: Implement `get_route_waypoints` in `agent/tools/google_directions.py`.
    - **Why**: Get waypoints along driving route A → B with ETAs.
    - **Depends on**: Step 34
    - **Output**: `agent/tools/google_directions.py`.
    - **Status**: ⬜ Not Started
    - **Done when**: Returns 5 waypoints for "Sofia → Plovdiv".

36. **Route Weather Orchestrator**
    - **What**: Implement `analyze_route_weather` in `agent/orchestrator.py`.
    - **Why**: Fetch weather for each waypoint and generate summary.
    - **Depends on**: Steps 27, 35
    - **Output**: Updated `agent/orchestrator.py` with route logic.
    - **Status**: ⬜ Not Started
    - **Done when**: Returns weather + warnings for each waypoint.

37. **New /route-weather Endpoint**
    - **What**: Add `POST /route-weather` endpoint.
    - **Why**: User asks "What's the weather Sofia to Plovdiv?"
    - **Depends on**: Step 36
    - **Output**: `RouteWeatherRequest`, `RouteWeatherResponse` schemas + route.
    - **Status**: ⬜ Not Started
    - **Done when**: Swagger shows endpoint and returns waypoint forecasts.

---

## Part 8: Final Integration (Steps 38-40) 🎯

38. **Update OpenAPI**
    - **What**: Regenerate `openapi.json` with all new endpoints.
    - **Why**: Copilot Studio needs updated API definition.
    - **Depends on**: Steps 28, 31, 37
    - **Output**: Updated `service/openapi.json` and `openapi_copilot.json`.
    - **Status**: ⬜ Not Started
    - **Done when**: OpenAPI includes `/geocode`, `/route-weather`, updated `/analyze`.

39. **Update Copilot Studio**
    - **What**: Re-import OpenAPI, add new tools, update instructions.
    - **Why**: Enable Copilot to use all new features.
    - **Depends on**: Step 38
    - **Output**: 3 new tools in Copilot Studio.
    - **Status**: ⬜ Not Started
    - **Done when**: All tools work in Copilot chat.

40. **Final Testing & Release**
    - **What**: End-to-end tests, cleanup, tag v1.0.0.
    - **Why**: Ensure a polished, complete handoff.
    - **Depends on**: All previous steps
    - **Output**: Release tag, final checklist.
    - **Status**: ⬜ Not Started
    - **Done when**: All deliverables are present and validated.

---

## Progress Summary

| Part | Steps | Completed | Status |
|------|-------|-----------|--------|
| 1. Foundation | 1-3 | 3/3 | ✅ 100% |
| 2. Core API | 4-15 | 12/12 | ✅ 100% |
| 3. Deployment | 16-26 | 5/11 | 🟨 45% |
| 4. Snow Data | 27-28 | 0/2 | ⬜ 0% |
| 5. Geocoding | 29-31 | 0/3 | ⬜ 0% |
| 6. Enhanced Analyze | 32-33 | 0/2 | ⬜ 0% |
| 7. Route Weather | 34-37 | 0/4 | ⬜ 0% |
| 8. Final Integration | 38-40 | 0/3 | ⬜ 0% |
| **TOTAL** | **1-40** | **20/40** | **50%** |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    COPILOT STUDIO                           │
│                   (OutdoorMate Agent)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │ OpenAPI 3.0
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Service                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ /analyze │ │ /geocode │ │  /route  │ │  /apod/today  │  │
│  │          │ │          │ │ -weather │ │               │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────────────┘  │
└───────┼────────────┼────────────┼───────────────────────────┘
        │            │            │
        ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Agent Orchestrator                      │
│  ┌────────┐ ┌────────┐ ┌─────────┐ ┌────────┐ ┌─────────┐  │
│  │Planner │ │Validate│ │ Compute │ │ Cache  │ │   LLM   │  │
│  └────────┘ └────────┘ └─────────┘ └────────┘ └─────────┘  │
└───────┬────────────┬────────────┬───────────────────────────┘
        │            │            │
        ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                      External APIs                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ │
│  │ Open-Meteo │ │  Google    │ │  GitHub    │ │   NASA   │ │
│  │  Weather   │ │   Maps     │ │  Models    │ │   APOD   │ │
│  │ Air Quality│ │ Geocoding  │ │   (LLM)    │ │          │ │
│  │   Snow     │ │ Directions │ │            │ │          │ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints Summary

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/` | GET | Health check | 🟩 Done |
| `/analyze` | POST | Air + weather + snow + guidance | 🟩 Done (snow pending) |
| `/apod/today` | GET | NASA Astronomy Picture of the Day | 🟩 Done |
| `/geocode` | POST | Place name → coordinates | ⬜ Pending |
| `/route-weather` | POST | Weather along driving route | ⬜ Pending |

---

## Environment Variables (Complete)

```env
# === GitHub Models (LLM) ===
GITHUB_MODELS_TOKEN=your_github_pat
GITHUB_MODELS_MODEL=gpt-4o-mini

# === NASA (optional) ===
NASA_API_KEY=DEMO_KEY

# === Google Maps (for geocoding + routes) ===
GOOGLE_MAPS_API_KEY=your_google_api_key

# === Performance ===
CACHE_TTL_SECONDS=600
HTTP_TIMEOUT_SECONDS=10.0
LLM_TIMEOUT_SECONDS=15.0
```

---

## Current Public API

**URL**: `https://humble-winner-g7wwrw4rp9rcxvq-8000.app.github.dev`

**Swagger**: `https://humble-winner-g7wwrw4rp9rcxvq-8000.app.github.dev/docs`

---

## Milestones

| Milestone | Steps | Target Date | Status |
|-----------|-------|-------------|--------|
| **M1: Core API** | 1-15 | ✅ 23 Dec 2024 | 🟩 Done |
| **M2: Copilot Live** | 21, 23, 25, 26 | ✅ 23 Dec 2024 | 🟩 Done |
| **M3: Snow Data** | 27-28 | TBD | ⬜ Pending |
| **M4: Geocoding** | 29-33 | TBD | ⬜ Pending |
| **M5: Route Weather** | 34-37 | TBD | ⬜ Pending |
| **M6: v1.0 Release** | 38-40 | TBD | ⬜ Pending |

---
