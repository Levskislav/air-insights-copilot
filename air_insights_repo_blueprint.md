# Repo Blueprint + Technical Execution Steps — Agentic “Air & Insights Copilot” (EN)

This document is a **literal executable runbook**:  
**what to do at each step, how, where (files/folders), and with which commands** to implement the task.

> I choose **Track B (Open & free) first**: Python **FastAPI** + minimal Web UI/CLI.  
> Reason: this is the fastest way to prove that **the API contract, cache, retry/backoff, validation, and GitHub Models LLM** all work.  
> Then the **same OpenAPI** can be imported into Copilot Studio (Track A) without rewriting.

---

## 0) Prerequisites (before you start)

### 0.1 Local software
- Python **3.10+** (3.11 recommended)
- `git`
- Terminal/PowerShell

### 0.2 Access/keys
- **GitHub token** (PAT) with access to GitHub Models (for free inference)
- (Optional) **NASA API key** or use `DEMO_KEY`

### 0.3 Minimal decisions
- Guidance language: EN or BG (here I assume EN for Copilot-friendliness, but you can use BG)
- GitHub Models model: pick a fast/cheap one (e.g., a *small* model)

---

## 1) Repo structure (exactly how it should look)

Target structure (fulfills deliverables: `service/`, `agent/`, `tests/`, `docs/`):

```text
air-insights-copilot/
  service/
    main.py
    routes.py
    schemas.py
    openapi.json              # generated and committed
    __init__.py
  agent/
    orchestrator.py
    planner.py
    validate.py
    compute.py
    cache.py
    retry.py
    prompts/
      guidance_system.txt
      guidance_user_template.txt
    tools/
      open_meteo.py
      nasa_apod.py
      github_models_llm.py
    __init__.py
  ui/
    web/
      index.html
      app.js
      styles.css
  tests/
    test_validate.py
    test_compute.py
    test_integration_analyze.py
  docs/
    README.md
    copilot_tool_snippet.md
    runbook.md
  .env                    # NOT committed
  .env.example
  requirements.txt
  pyproject.toml          # optional
  .gitignore
```

---

## 2) Step by step: create the project (commands)

### 2.1 Create folder and git repo
```bash
mkdir air-insights-copilot
cd air-insights-copilot
git init
mkdir -p service agent/{prompts,tools} ui/web tests docs
touch service/{__init__.py,main.py,routes.py,schemas.py}
touch agent/{__init__.py,orchestrator.py,planner.py,validate.py,compute.py,cache.py,retry.py}
touch agent/prompts/{guidance_system.txt,guidance_user_template.txt}
touch agent/tools/{open_meteo.py,nasa_apod.py,github_models_llm.py}
touch ui/web/{index.html,app.js,styles.css}
touch tests/{test_validate.py,test_compute.py,test_integration_analyze.py}
touch docs/{README.md,copilot_tool_snippet.md,runbook.md}
touch requirements.txt .env.example .gitignore
```

### 2.2 `.gitignore`
**File:** `.gitignore`
```gitignore
.venv/
__pycache__/
*.pyc
.env
.DS_Store
.pytest_cache/
service/openapi.json
```
> Note: you may decide to commit `service/openapi.json` (recommended for Copilot Studio import).  
> If you will commit it — remove `service/openapi.json` from `.gitignore`.

### 2.3 Python venv + installs
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
```

---

## 3) Dependencies (requirements)

**File:** `requirements.txt`  
(minimal but sufficient for the requirements)
```txt
fastapi>=0.110
uvicorn[standard]>=0.27
httpx>=0.27
python-dotenv>=1.0
cachetools>=5.3
pytest>=8.0
```

Install:
```bash
pip install -r requirements.txt
```

---

## 4) Configuration and secrets (.env)

### 4.1 `.env.example` (committed)
**File:** `.env.example`
```env
# LLM (GitHub Models)
GITHUB_MODELS_TOKEN=replace_me
GITHUB_MODELS_MODEL=replace_me_with_model_name

# Optional: NASA APOD
NASA_API_KEY=DEMO_KEY

# Service behavior
CACHE_TTL_SECONDS=600
HTTP_TIMEOUT_SECONDS=1.0
LLM_TIMEOUT_SECONDS=1.5
```

### 4.2 `.env` (NOT committed)
Copy and fill:
```bash
cp .env.example .env
```

---

## 5) API contract: schemas (Pydantic models)

**File:** `service/schemas.py`

### What to do
- Define input/output models exactly per requirement:
  - `POST /analyze` input: `{ latitude, longitude, hours }`
  - output: `{ pm25_avg, pm10_avg, temp_avg, guidance_text }`
- (Optional) `GET /apod/today` output: `{ title, url, explanation }`

### Pseudo-code (structure)
```python
from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    latitude: float
    longitude: float
    hours: int = Field(ge=1, le=72)

class AnalyzeResponse(BaseModel):
    pm25_avg: float | None
    pm10_avg: float | None
    temp_avg: float | None
    guidance_text: str

class ApodResponse(BaseModel):
    title: str
    url: str
    explanation: str
```

> Why: Pydantic gives you **validation** and **automatic OpenAPI**.

---

## 6) Service layer: FastAPI app + routing

### 6.1 `service/main.py`
**What it does:** creates the FastAPI app and includes routes.  

**Pseudo-code:**
```python
from fastapi import FastAPI
from service.routes import router

app = FastAPI(title="Air & Insights Copilot", version="0.1.0")
app.include_router(router)
```

### 6.2 `service/routes.py`
**What it does:** defines endpoints and calls the agent/orchestrator.

**Pseudo-code:**
```python
from fastapi import APIRouter
from service.schemas import AnalyzeRequest, AnalyzeResponse, ApodResponse
from agent.orchestrator import analyze_air_and_weather, apod_today

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    # 1) Validate bounds (lat/lon, hours already constrained)
    # 2) Call orchestrator
    return await analyze_air_and_weather(req.latitude, req.longitude, req.hours)

@router.get("/apod/today", response_model=ApodResponse)
async def get_apod_today():
    return await apod_today()
```

> Why: the service layer stays **thin** (HTTP only), the “smart” logic is in `agent/`.

---

## 7) Agent layer: orchestrator (agentic flow)

### 7.1 `agent/orchestrator.py` — **The heart of the agent**
Here is the flow: **plan → cache → fetch tools → validate → compute → LLM → cache → respond**.

**Pseudo-code (important, follows the requirement literally):**
```python
from agent.planner import plan_for_analyze
from agent.validate import validate_lat_lon, validate_open_meteo_payload
from agent.compute import safe_avg
from agent.cache import ttl_cache_get, ttl_cache_set, cache_key
from agent.tools.open_meteo import fetch_air_quality, fetch_weather
from agent.tools.github_models_llm import generate_guidance_text

ATTRIBUTION = "Weather data by Open-Meteo.com"

async def analyze_air_and_weather(lat: float, lon: float, hours: int):
    # Validate input (lat/lon bounds)
    validate_lat_lon(lat, lon)

    # Cache
    key = cache_key(lat, lon, hours)
    cached = ttl_cache_get(key)
    if cached:
        return cached

    # Plan
    plan = plan_for_analyze(lat, lon, hours)
    # plan might be {"need_air": True, "need_weather": True}

    # Fetch (with retry/backoff inside tools)
    air_json = await fetch_air_quality(lat, lon, hours) if plan["need_air"] else None
    wx_json  = await fetch_weather(lat, lon, hours) if plan["need_weather"] else None

    # Validate tool outputs (shape + presence)
    air_data, wx_data, quality_flags = validate_open_meteo_payload(air_json, wx_json, hours)

    # Compute averages safely
    pm25_avg = safe_avg(air_data.pm25) if air_data else None
    pm10_avg = safe_avg(air_data.pm10) if air_data else None
    temp_avg = safe_avg(wx_data.temp) if wx_data else None

    # Reason with LLM (fallback if LLM fails)
    guidance = await generate_guidance_text(
        pm25_avg=pm25_avg,
        pm10_avg=pm10_avg,
        temp_avg=temp_avg,
        hours=hours,
        lat=lat, lon=lon,
        quality_flags=quality_flags
    )
    guidance = guidance.strip() + f"\n\n{ATTRIBUTION}"

    resp = {
        "pm25_avg": pm25_avg,
        "pm10_avg": pm10_avg,
        "temp_avg": temp_avg,
        "guidance_text": guidance
    }

    # Cache store (10 minutes)
    ttl_cache_set(key, resp)
    return resp
```

**Why:**  
- You separate the “orchestrator” so you have real **agentic behavior** (not just a single function call).

---

## 8) Planner (planning)

**File:** `agent/planner.py`

### What to do
- Even if simple, the planner gives the “agent feel”:
  - for `/analyze` → you need both air + weather
  - for other intents (if you later add chat) → it chooses which tools to call

**Pseudo-code:**
```python
def plan_for_analyze(lat, lon, hours):
    return {
        "need_air": True,
        "need_weather": True,
        "variables_air": ["pm2_5", "pm10"],
        "variables_weather": ["temperature_2m"]
    }
```

---

## 9) Validation (quality gates)

### 9.1 `agent/validate.py`

**What to do**
1) Validate lat/lon bounds:
- lat ∈ [-90..90]
- lon ∈ [-180..180]

2) Validate response shape:
- `hourly` exists
- arrays for required variables are present
- there is at least 1 value (or mark as “sparse data”)

**Pseudo-code:**
```python
class DataQualityFlags:
    sparse_air: bool
    sparse_weather: bool
    missing_fields: list[str]

def validate_lat_lon(lat, lon):
    if lat < -90 or lat > 90: raise ValueError("latitude out of range")
    if lon < -180 or lon > 180: raise ValueError("longitude out of range")

def validate_open_meteo_payload(air_json, wx_json, hours):
    flags = DataQualityFlags(...)
    # Extract arrays safely and slice to 'hours'
    # Return typed objects: air_data(pm25, pm10), wx_data(temp), flags
```

> Why: the requirement says “validation” and “mention uncertainty if data is sparse”.

---

## 10) Computations (safe averages)

**File:** `agent/compute.py`

**What to do**
- `safe_avg(values)`:
  - ignores `None`
  - if there are no valid values → return `None`

**Pseudo-code:**
```python
def safe_avg(values: list[float | None]) -> float | None:
    nums = [v for v in values if v is not None]
    if not nums:
        return None
    return sum(nums) / len(nums)
```

---

## 11) Cache (10 min TTL)

**File:** `agent/cache.py`

### What to do
- TTL cache with key `<lat, lon, hours>` for 10 minutes.
- Use `cachetools.TTLCache` (simple and robust).

**Pseudo-code:**
```python
from cachetools import TTLCache

_cache = TTLCache(maxsize=1024, ttl=CACHE_TTL_SECONDS)

def cache_key(lat, lon, hours):
    return f"{lat}:{lon}:{hours}"

def ttl_cache_get(key):
    return _cache.get(key)

def ttl_cache_set(key, value):
    _cache[key] = value
```

> Why: the requirement is “Cache results for 10 minutes”.

---

## 12) Retry/backoff + timeouts (for HTTP calls)

**File:** `agent/retry.py`

### What to do
- Unified function `request_with_retry(...)`:
  - max 3 tries
  - exponential backoff (0.2s, 0.5s, 1.2s)
  - request timeout

**Pseudo-code:**
```python
import asyncio
import httpx

async def request_with_retry(method, url, params=None, headers=None, json=None, timeout=1.0):
    delays = [0.2, 0.5, 1.2]
    last_err = None
    for i in range(len(delays) + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.request(method, url, params=params, headers=headers, json=json)
            if r.status_code in (429, 500, 502, 503, 504):
                raise RuntimeError(f"retryable http {r.status_code}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            if i < len(delays):
                await asyncio.sleep(delays[i])
            else:
                raise last_err
```

> Why: external APIs sometimes return 429/5xx or there are network hiccups.

---

## 13) Tools: Open-Meteo (weather + air quality)

**File:** `agent/tools/open_meteo.py`

### What to do
Implement 2 functions:

1) `fetch_air_quality(lat, lon, hours)`
2) `fetch_weather(lat, lon, hours)`

**Pseudo-code:**
```python
from agent.retry import request_with_retry

AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_URL  = "https://api.open-meteo.com/v1/forecast"

async def fetch_air_quality(lat, lon, hours):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm2_5,pm10",
        "forecast_hours": hours,   # if API does not return enough → fallback: request more and slice
        "timezone": "auto"
    }
    return await request_with_retry("GET", AIR_URL, params=params)

async def fetch_weather(lat, lon, hours):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m",
        "forecast_hours": hours,
        "timezone": "auto"
    }
    return await request_with_retry("GET", WX_URL, params=params)
```

**Fallback idea (for robustness):**
- if arrays are shorter than `hours`, make a second call with `forecast_days=3` and slice the first N values.  
(This way you are not 100% dependent on `forecast_hours`.)

---

## 14) Tools: NASA APOD (optional)

**File:** `agent/tools/nasa_apod.py`

**Pseudo-code:**
```python
from agent.retry import request_with_retry
import os

APOD_URL = "https://api.nasa.gov/planetary/apod"

async def fetch_apod_today():
    key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    params = {"api_key": key}
    return await request_with_retry("GET", APOD_URL, params=params)
```

---

## 15) Tools: GitHub Models LLM (free inference)

**File:** `agent/tools/github_models_llm.py`

### What to do
- Implement `generate_guidance_text(...)` which:
  - loads prompts from `agent/prompts/`
  - does a `POST` to GitHub Models OpenAI-compatible endpoint
  - if it fails → returns **fallback** (rule-based) text

**Pseudo-code:**
```python
import os
from agent.retry import request_with_retry

GITHUB_URL = "https://models.github.ai/inference/chat/completions"

def build_messages(pm25_avg, pm10_avg, temp_avg, hours, quality_flags):
    system = load("agent/prompts/guidance_system.txt")
    user_tmpl = load("agent/prompts/guidance_user_template.txt")
    user = user_tmpl.format(
        pm25=pm25_avg, pm10=pm10_avg, temp=temp_avg, hours=hours,
        sparse_air=quality_flags.sparse_air, sparse_weather=quality_flags.sparse_weather
    )
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]

async def generate_guidance_text(...):
    token = os.environ["GITHUB_MODELS_TOKEN"]
    model = os.getenv("GITHUB_MODELS_MODEL")
    messages = build_messages(...)

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"model": model, "messages": messages, "temperature": 0.3}

    try:
        resp = await request_with_retry("POST", GITHUB_URL, headers=headers, json=body, timeout=LLM_TIMEOUT)
        return resp["choices"][0]["message"]["content"]
    except Exception:
        return fallback_guidance(pm25_avg, pm10_avg, temp_avg, hours, quality_flags)
```

**Why fallback:**  
The LLM can be slow / return an error. The API should work **even without the LLM** (more stable UX).

---

## 16) Prompt library (LLM instructions)

### 16.1 `agent/prompts/guidance_system.txt`
**Goal:** defines the role and rules.

Example (short):
```txt
You are a practical assistant for outdoor activity decisions.
Use the provided PM2.5, PM10, and temperature averages for the next N hours.

Rules:
- Give actionable guidance in 3-6 sentences.
- Include a short justification (1-2 sentences).
- If data is missing/sparse, mention uncertainty and suggest caution.
- Avoid medical claims; suggest general precautions.
```

### 16.2 `agent/prompts/guidance_user_template.txt`
**Goal:** feeds the “data” to the LLM in a stable way.

Example:
```txt
Location: lat={lat}, lon={lon}
Window: next {hours} hours

Averages:
- PM2.5: {pm25}
- PM10: {pm10}
- Temperature (2m): {temp}

Data quality:
- sparse_air={sparse_air}
- sparse_weather={sparse_weather}

Question: Is it safe to run outdoors during this window?
Provide guidance and precautions.
```

---

## 17) Minimal Web UI (Track B)

### 17.1 `ui/web/index.html`
- Inputs: latitude, longitude, hours
- Button “Analyze”
- Result display area

### 17.2 `ui/web/app.js`
- `fetch("http://localhost:8000/analyze", {method:"POST", ...})`
- Displays pm25_avg, pm10_avg, temp_avg and guidance_text

> If you want to serve it from FastAPI:
- add `StaticFiles` and a route for `/` (optional)

---

## 18) Run locally

### 18.1 Run service
```bash
uvicorn service.main:app --reload --port 8000
```

### 18.2 Check OpenAPI and docs
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### 18.3 Export OpenAPI file (for Copilot Studio import)
```bash
curl -s http://localhost:8000/openapi.json > service/openapi.json
```
> Commit it (recommended):
```bash
git add service/openapi.json
git commit -m "docs: add exported OpenAPI spec"
```

### 18.4 Demo request
```bash
curl -s -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"latitude":42.6977,"longitude":23.3219,"hours":6}'
```

---

## 19) Tests (unit + integration with stub)

### 19.1 `tests/test_validate.py`
**What to test**
- valid and invalid lat/lon
- hours boundaries (in schema)

Pseudo:
```python
import pytest
from agent.validate import validate_lat_lon

def test_lat_lon_ok():
    validate_lat_lon(42.0, 23.0)

def test_lat_out_of_range():
    with pytest.raises(ValueError):
        validate_lat_lon(200.0, 23.0)
```

### 19.2 `tests/test_compute.py`
Pseudo:
```python
from agent.compute import safe_avg

def test_safe_avg_ignores_none():
    assert safe_avg([1.0, None, 3.0]) == 2.0

def test_safe_avg_all_none():
    assert safe_avg([None, None]) is None
```

### 19.3 `tests/test_integration_analyze.py`
**Goal:** don’t call real external APIs; stub the tool functions instead.

Pseudo:
```python
from fastapi.testclient import TestClient
from service.main import app
import agent.tools.open_meteo as om
import agent.tools.github_models_llm as llm

def test_analyze_integration(monkeypatch):
    monkeypatch.setattr(om, "fetch_air_quality", fake_air)
    monkeypatch.setattr(om, "fetch_weather", fake_wx)
    monkeypatch.setattr(llm, "generate_guidance_text", fake_guidance)

    client = TestClient(app)
    r = client.post("/analyze", json={"latitude":42.6977,"longitude":23.3219,"hours":2})
    data = r.json()
    assert "Weather data by Open-Meteo.com" in data["guidance_text"]
    assert data["pm25_avg"] is not None
```

Run:
```bash
pytest -q
```

---

## 20) Logging and observability (minimum)

**Where:** `service/routes.py` and `agent/orchestrator.py`  
Add:
- request_id (uuid)
- log: cache hit/miss
- log: latency of Open-Meteo calls and LLM
- traceback on exception

Pseudo:
```python
import logging, time, uuid
log = logging.getLogger("air_insights")

rid = str(uuid.uuid4())
t0 = time.time()
log.info("analyze start rid=%s lat=%s lon=%s hours=%s", rid, lat, lon, hours)
...
log.info("cache hit rid=%s", rid)
...
log.exception("analyze failed rid=%s", rid)
```

---

## 21) Copilot Studio integration (Track A) — what to prepare

### 21.1 What you need
- public HTTPS URL for your service (deployed to Azure App Service/Container Apps, etc.)
- `service/openapi.json` or YAML

### 21.2 `docs/copilot_tool_snippet.md`
Include:
- **Tool name**: `analyzeAirAndWeather`
- **When to use**: when the user asks about air quality / PM2.5 / PM10 / temperature / “safe to run”
- input/output examples

---

## 22) Demo prompts (required)

1) “What’s the PM2.5 and temperature around 42.6977, 23.3219 for the next 6 hours and should I run outdoors?”
2) “Show today’s NASA APOD and summarize in 2 lines.”

---

## 23) MVP checklist (to get to working state fast)

1) (✔) Repo structure + dependencies + .env  
2) (✔) `/analyze` works end-to-end (Open-Meteo → averages → LLM → response + attribution)  
3) (✔) 10-minute cache  
4) (✔) Retry/backoff  
5) (✔) Tests for validate + avg + integration stub  
6) (✔) Screenshot from Web UI/CLI  

---

## 24) Notes for “exactly per the spec”

- **Must use Open-Meteo** for weather + air quality, and add attribution:  
  `Weather data by Open-Meteo.com`
- **LLM reasoning**: use GitHub Models free inference
- **Cache**: 10 minutes for `<lat,lon,hours>`
- **Validation gates**: lat/lon bounds, hours [1..72]
- **Performance**: cached p95 < 2s (with in-memory cache this is easy)

---


