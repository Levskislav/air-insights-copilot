# Technical Execution Steps (EN) — OutdoorMate

This file is a **hands-on runbook**: exactly what to do, where, and how to implement the project.  
Target: **Track A** (FastAPI + Copilot Studio integration).

> **Project renamed**: Air & Insights Copilot → **OutdoorMate**

---

## Current Status (23 Dec 2025)

### ✅ Completed (MVP)
| Step | Description | Status |
|------|-------------|--------|
| 1-15 | Core API (air quality, weather, LLM guidance) | ✅ Done |
| 21 | Export OpenAPI 3.0 | ✅ Done |
| 22 | GitHub Codespaces deployment | ✅ Done |
| 23 | Copilot tool snippet | ✅ Done |
| 25 | Copilot Studio integration | ✅ Done |

### 📍 Public API URL
```
https://humble-winner-g7wwrw4rp9rcxvq-8000.app.github.dev
```

### 🎯 Working Endpoints
- `POST /analyze` - Air quality + weather + AI guidance
- `GET /apod/today` - NASA Astronomy Picture of the Day
- `GET /` - Health check

---

## Planned Features (Phase 2)

### Feature A: Snow Data 🌨️
- **What**: Snowfall and snow depth tracking
- **API**: Open-Meteo (free, no key needed)
- **Endpoint**: Extend `/analyze` or new `/snow`

### Feature B: Geocoding 📍
- **What**: Convert place names to coordinates
- **API**: Google Maps Geocoding API (requires key)
- **Endpoint**: New `/geocode` or integrated into `/analyze`
- **Benefit**: User types "Sofia" instead of coordinates

### Feature C: Route Weather 🚗
- **What**: Weather forecast along a driving route (A → B)
- **APIs**: Google Directions API + Open-Meteo
- **Endpoint**: New `/route-weather`
- **Use case**: "What's the weather on my trip from Sofia to Plovdiv?"

---

## 1) Create the repo and folders

```bash
mkdir air-insights-copilot
cd air-insights-copilot
git init

mkdir -p service agent/{prompts,tools} ui/web tests docs screenshots
touch requirements.txt .env.example .gitignore
touch service/{__init__.py,main.py,routes.py,schemas.py}
touch agent/{__init__.py,orchestrator.py,planner.py,validate.py,compute.py,cache.py,retry.py}
touch agent/prompts/{guidance_system.txt,guidance_user_template.txt}
touch agent/tools/{open_meteo.py,nasa_apod.py,github_models_llm.py}
touch ui/web/{index.html,app.js,styles.css}
touch docs/{README.md,copilot_tool_snippet.md,runbook.md}
touch tests/{test_validate.py,test_compute.py,test_integration_analyze.py}
```

---

## 2) Add dependencies

**requirements.txt**
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
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

---

## 3) Configure environment variables

**.env.example**
```env
GITHUB_MODELS_TOKEN=replace_me
GITHUB_MODELS_MODEL=replace_me

NASA_API_KEY=DEMO_KEY

CACHE_TTL_SECONDS=600
HTTP_TIMEOUT_SECONDS=1.0
LLM_TIMEOUT_SECONDS=1.5
```

Create local `.env`:
```bash
cp .env.example .env
```

---

## 4) Implement API schemas (service/schemas.py)

**service/schemas.py**
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

---

## 5) Implement FastAPI app and routes

**service/main.py**
```python
from fastapi import FastAPI
from service.routes import router

app = FastAPI(title="Air & Insights Copilot", version="0.1.0")
app.include_router(router)
```

**service/routes.py**
```python
from fastapi import APIRouter
from service.schemas import AnalyzeRequest, AnalyzeResponse, ApodResponse
from agent.orchestrator import analyze_air_and_weather, apod_today

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    return await analyze_air_and_weather(req.latitude, req.longitude, req.hours)

@router.get("/apod/today", response_model=ApodResponse)
async def apod():
    return await apod_today()
```

---

## 6) Implement retry/backoff helper

**agent/retry.py**
```python
import asyncio
import httpx

RETRY_STATUS = {429, 500, 502, 503, 504}

async def request_with_retry(method: str, url: str, *, params=None, headers=None, json=None, timeout: float = 1.0):
    delays = [0.2, 0.5, 1.2]
    last_err = None
    for i in range(len(delays) + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.request(method, url, params=params, headers=headers, json=json)
            if r.status_code in RETRY_STATUS:
                raise RuntimeError(f"retryable http status {r.status_code}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            if i < len(delays):
                await asyncio.sleep(delays[i])
            else:
                raise last_err
```

---

## 7) Implement Open-Meteo tools (weather + air quality)

**agent/tools/open_meteo.py**
```python
from agent.retry import request_with_retry
import os

AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_URL  = "https://api.open-meteo.com/v1/forecast"

async def fetch_air_quality(lat: float, lon: float, hours: int):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm2_5,pm10",
        "forecast_hours": hours,
        "timezone": "auto"
    }
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "1.0"))
    return await request_with_retry("GET", AIR_URL, params=params, timeout=timeout)

async def fetch_weather(lat: float, lon: float, hours: int):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m",
        "forecast_hours": hours,
        "timezone": "auto"
    }
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "1.0"))
    return await request_with_retry("GET", WX_URL, params=params, timeout=timeout)
```

---

## 8) Implement NASA APOD tool (optional)

**agent/tools/nasa_apod.py**
```python
from agent.retry import request_with_retry
import os

APOD_URL = "https://api.nasa.gov/planetary/apod"

async def fetch_apod_today():
    key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    params = {"api_key": key}
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "1.0"))
    return await request_with_retry("GET", APOD_URL, params=params, timeout=timeout)
```

---

## 9) Implement input + payload validation

**agent/validate.py**
```python
from dataclasses import dataclass
from typing import Any

@dataclass
class QualityFlags:
    sparse_air: bool = False
    sparse_weather: bool = False
    missing_fields: list[str] = None

def validate_lat_lon(lat: float, lon: float):
    if lat < -90 or lat > 90:
        raise ValueError("latitude out of range [-90..90]")
    if lon < -180 or lon > 180:
        raise ValueError("longitude out of range [-180..180]")

def _get_hourly_array(payload: dict, key: str):
    hourly = payload.get("hourly") if isinstance(payload, dict) else None
    if not hourly or key not in hourly:
        return None
    return hourly.get(key)

def validate_open_meteo_payload(air_json: dict | None, wx_json: dict | None, hours: int):
    flags = QualityFlags(missing_fields=[])

    pm25 = pm10 = temp = None

    if air_json:
        pm25 = _get_hourly_array(air_json, "pm2_5")
        pm10 = _get_hourly_array(air_json, "pm10")
        if pm25 is None: flags.missing_fields.append("pm2_5")
        if pm10 is None: flags.missing_fields.append("pm10")
        flags.sparse_air = (not pm25) or (len(pm25) < 1)

    if wx_json:
        temp = _get_hourly_array(wx_json, "temperature_2m")
        if temp is None: flags.missing_fields.append("temperature_2m")
        flags.sparse_weather = (not temp) or (len(temp) < 1)

    # slice to requested window (if arrays exist)
    pm25 = pm25[:hours] if pm25 else pm25
    pm10 = pm10[:hours] if pm10 else pm10
    temp = temp[:hours] if temp else temp

    return {"pm25": pm25, "pm10": pm10, "temp": temp}, flags
```

---

## 10) Implement safe averages

**agent/compute.py**
```python
from typing import Iterable

def safe_avg(values: list[float | None] | None) -> float | None:
    if not values:
        return None
    nums = [v for v in values if v is not None]
    if not nums:
        return None
    return sum(nums) / len(nums)
```

---

## 11) Implement TTL cache (10 minutes)

**agent/cache.py**
```python
from cachetools import TTLCache
import os

TTL = int(os.getenv("CACHE_TTL_SECONDS", "600"))
_cache = TTLCache(maxsize=1024, ttl=TTL)

def cache_key(lat: float, lon: float, hours: int) -> str:
    # round to reduce cache fragmentation
    return f"{round(lat, 4)}:{round(lon, 4)}:{hours}"

def cache_get(key: str):
    return _cache.get(key)

def cache_set(key: str, value):
    _cache[key] = value
```

---

## 12) Implement minimal planner

**agent/planner.py**
```python
def plan_for_analyze(lat: float, lon: float, hours: int) -> dict:
    return {
        "need_air": True,
        "need_weather": True,
        "air_vars": ["pm2_5", "pm10"],
        "weather_vars": ["temperature_2m"]
    }
```

---

## 13) Implement GitHub Models LLM tool

**agent/tools/github_models_llm.py**
```python
import os
from agent.retry import request_with_retry

GITHUB_URL = "https://models.github.ai/inference/chat/completions"

def _load(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _build_messages(pm25_avg, pm10_avg, temp_avg, hours, lat, lon, flags):
    system = _load("agent/prompts/guidance_system.txt")
    user_tmpl = _load("agent/prompts/guidance_user_template.txt")
    user = user_tmpl.format(
        lat=lat, lon=lon, hours=hours,
        pm25=pm25_avg, pm10=pm10_avg, temp=temp_avg,
        sparse_air=flags.sparse_air, sparse_weather=flags.sparse_weather,
        missing_fields=",".join(flags.missing_fields or [])
    )
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]

def fallback_guidance(pm25_avg, pm10_avg, temp_avg, hours, flags) -> str:
    # very simple rule-based fallback
    parts = []
    parts.append(f"Window: next {hours} hours.")
    if pm25_avg is None or temp_avg is None:
        parts.append("Data is incomplete; consider a cautious approach or check again later.")
    else:
        parts.append("Consider moderating intensity if air feels irritating or if you have sensitivities.")
    parts.append("If you notice symptoms, stop and move indoors.")
    return " ".join(parts)

async def generate_guidance_text(*, pm25_avg, pm10_avg, temp_avg, hours, lat, lon, flags):
    token = os.getenv("GITHUB_MODELS_TOKEN")
    model = os.getenv("GITHUB_MODELS_MODEL")
    if not token or not model:
        return fallback_guidance(pm25_avg, pm10_avg, temp_avg, hours, flags)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": _build_messages(pm25_avg, pm10_avg, temp_avg, hours, lat, lon, flags),
        "temperature": 0.3
    }
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "1.5"))
    try:
        resp = await request_with_retry("POST", GITHUB_URL, headers=headers, json=body, timeout=timeout)
        return resp["choices"][0]["message"]["content"]
    except Exception:
        return fallback_guidance(pm25_avg, pm10_avg, temp_avg, hours, flags)
```

---

## 14) Implement prompt library

**agent/prompts/guidance_system.txt**
```txt
You are a practical assistant for outdoor activity decisions.
Use the provided PM2.5, PM10, and temperature averages for the next N hours.

Rules:
- Provide actionable guidance in 3–6 sentences.
- Include a short justification (1–2 sentences).
- If data is missing/sparse, mention uncertainty and suggest caution.
- Avoid medical claims; suggest general precautions.
```

**agent/prompts/guidance_user_template.txt**
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
- missing_fields={missing_fields}

Question: Is it safe to run outdoors during this window?
Provide guidance and precautions.
```

---

## 15) Implement the orchestrator (agent/orchestrator.py)

**agent/orchestrator.py**
```python
from agent.planner import plan_for_analyze
from agent.validate import validate_lat_lon, validate_open_meteo_payload
from agent.compute import safe_avg
from agent.cache import cache_key, cache_get, cache_set
from agent.tools.open_meteo import fetch_air_quality, fetch_weather
from agent.tools.github_models_llm import generate_guidance_text
from agent.tools.nasa_apod import fetch_apod_today

ATTRIBUTION = "Weather data by Open-Meteo.com"

async def analyze_air_and_weather(lat: float, lon: float, hours: int):
    validate_lat_lon(lat, lon)

    key = cache_key(lat, lon, hours)
    cached = cache_get(key)
    if cached:
        return cached

    plan = plan_for_analyze(lat, lon, hours)

    air_json = await fetch_air_quality(lat, lon, hours) if plan["need_air"] else None
    wx_json = await fetch_weather(lat, lon, hours) if plan["need_weather"] else None

    data, flags = validate_open_meteo_payload(air_json, wx_json, hours)

    pm25_avg = safe_avg(data.get("pm25"))
    pm10_avg = safe_avg(data.get("pm10"))
    temp_avg = safe_avg(data.get("temp"))

    guidance = await generate_guidance_text(
        pm25_avg=pm25_avg, pm10_avg=pm10_avg, temp_avg=temp_avg,
        hours=hours, lat=lat, lon=lon, flags=flags
    )
    guidance = (guidance or "").strip()
    if ATTRIBUTION not in guidance:
        guidance = guidance + ("\n\n" if guidance else "") + ATTRIBUTION

    resp = {
        "pm25_avg": pm25_avg,
        "pm10_avg": pm10_avg,
        "temp_avg": temp_avg,
        "guidance_text": guidance,
    }
    cache_set(key, resp)
    return resp

async def apod_today():
    apod = await fetch_apod_today()
    return {
        "title": apod.get("title", ""),
        "url": apod.get("url", ""),
        "explanation": apod.get("explanation", ""),
    }
```

---

## 16) Minimal web UI (optional but recommended)

**ui/web/index.html**
```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Air & Insights Copilot (Demo)</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <h1>Air & Insights Copilot</h1>

  <div class="card">
    <label>Latitude <input id="lat" value="42.6977" /></label>
    <label>Longitude <input id="lon" value="23.3219" /></label>
    <label>Hours (1..72) <input id="hours" value="6" /></label>
    <button id="btn">Analyze</button>
  </div>

  <pre id="out" class="card"></pre>

  <script src="app.js"></script>
</body>
</html>
```

**ui/web/app.js**
```js
const out = document.getElementById("out");
document.getElementById("btn").addEventListener("click", async () => {
  out.textContent = "Loading...";
  const body = {
    latitude: Number(document.getElementById("lat").value),
    longitude: Number(document.getElementById("lon").value),
    hours: Number(document.getElementById("hours").value),
  };
  const res = await fetch("http://localhost:8000/analyze", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body),
  });
  out.textContent = JSON.stringify(await res.json(), null, 2);
});
```

**ui/web/styles.css**
```css
body { font-family: sans-serif; margin: 24px; }
.card { border: 1px solid #ddd; padding: 12px; margin: 12px 0; }
label { display: block; margin: 8px 0; }
pre { white-space: pre-wrap; }
```

---

## 17) Run locally

Start API:
```bash
uvicorn service.main:app --reload --port 8000
```

Check docs:
- Swagger: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

Export OpenAPI file for Copilot:
```bash
curl -s http://localhost:8000/openapi.json > service/openapi.json
```

---

## 18) Tests

**tests/test_validate.py**
```python
import pytest
from agent.validate import validate_lat_lon

def test_lat_lon_ok():
    validate_lat_lon(42.0, 23.0)

def test_lat_out_of_range():
    with pytest.raises(ValueError):
        validate_lat_lon(200.0, 23.0)
```

**tests/test_compute.py**
```python
from agent.compute import safe_avg

def test_safe_avg():
    assert safe_avg([1.0, None, 3.0]) == 2.0

def test_safe_avg_none():
    assert safe_avg([None, None]) is None
```

**tests/test_integration_analyze.py** (stub external calls)
```python
from fastapi.testclient import TestClient
from service.main import app
import agent.tools.open_meteo as om
import agent.tools.github_models_llm as llm

def fake_air(*args, **kwargs):
    return {"hourly": {"pm2_5": [10, 20], "pm10": [15, 25]}}

def fake_wx(*args, **kwargs):
    return {"hourly": {"temperature_2m": [5, 7]}}

async def fake_guidance(**kwargs):
    return "Looks reasonable. Consider a moderate pace and reassess if conditions worsen."

def test_analyze(monkeypatch):
    monkeypatch.setattr(om, "fetch_air_quality", lambda *a, **k: fake_air())
    monkeypatch.setattr(om, "fetch_weather", lambda *a, **k: fake_wx())
    monkeypatch.setattr(llm, "generate_guidance_text", fake_guidance)

    client = TestClient(app)
    r = client.post("/analyze", json={"latitude":42.7, "longitude":23.3, "hours":2})
    data = r.json()
    assert r.status_code == 200
    assert "Weather data by Open-Meteo.com" in data["guidance_text"]
```

Run:
```bash
pytest -q
```

---

## 19) Docs and Copilot snippet

Create docs:
- `docs/README.md` — local run + env + demo prompts
- `docs/copilot_tool_snippet.md` — tool description, examples
- `docs/runbook.md` — operational notes (timeouts, cache, logs)

---

## 20) Track A (Copilot Studio) — what you do later

1) Deploy your API service publicly on HTTPS
2) Import `service/openapi.json` as a REST tool/action
3) Write a clear tool description (“Use when user asks about PM2.5/PM10, air quality, temperature, safe to run outdoors…”)
4) Enable Generative Orchestration and test the demo prompts
5) Save screenshots into `screenshots/`

---

### 20.1 Deploy via GitHub Codespaces (free option)

You can satisfy the “public HTTPS API” requirement using **GitHub Codespaces free tier** without paying for hosting:

- **Create a Codespace**
  - Push this repo to GitHub.
  - In GitHub, open the repo → **Code** → **Codespaces** → **Create Codespace**.

- **Install dependencies inside the Codespace**
  - Open the integrated terminal and run:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -U pip
    pip install -r requirements.txt
    cp .env.example .env   # then fill GITHUB_MODELS_TOKEN, etc.
    ```

- **Run the FastAPI service**
  - In the same terminal:
    ```bash
    uvicorn service.main:app --host 0.0.0.0 --port 8000
    ```
  - In the **Ports** panel of Codespaces, the port `8000` will appear.
  - Mark port `8000` as **Public**; GitHub will show a URL like  
    `https://8000-<random>.githubpreview.dev`.

- **Use this URL in Copilot Studio**
  - **Base URL** of the Tool: `https://8000-<random>.githubpreview.dev`
  - **OpenAPI URL**: `https://8000-<random>.githubpreview.dev/openapi.json`
  - Import the OpenAPI into Copilot Studio and configure the Tool using  
    `docs/copilot_tool_snippet.md` (tool name, when to call, examples).

- **Limitations (acceptable for this project)**
  - The URL is only live while the Codespace and `uvicorn` are running.
  - This is sufficient for:
    - configuring the Tool,
    - running demo prompts,
    - capturing screenshots or a short demo video.

---

# Phase 2: New Features Implementation

## 21) Feature A: Snow Data 🌨️

### 21.1) Update Open-Meteo tool for snow

**agent/tools/open_meteo.py** — add new function:
```python
async def fetch_snow(lat: float, lon: float, hours: int):
    """
    Fetch snowfall and snow depth from Open-Meteo.
    
    Returns:
        - snowfall: cm per hour (snow precipitation)
        - snow_depth: cm (accumulated snow on ground)
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "snowfall,snow_depth",
        "forecast_hours": hours,
        "timezone": "auto"
    }
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10.0"))
    return await request_with_retry("GET", WX_URL, params=params, timeout=timeout)
```

### 21.2) Update schemas

**service/schemas.py** — extend AnalyzeResponse:
```python
class AnalyzeResponse(BaseModel):
    pm25_avg: float | None
    pm10_avg: float | None
    temp_avg: float | None
    # NEW: Snow data
    snowfall_sum: float | None = Field(None, description="Total snowfall in cm")
    snow_depth_avg: float | None = Field(None, description="Average snow depth in cm")
    guidance_text: str
```

### 21.3) Update orchestrator

Add snow fetching to `analyze_air_and_weather()`:
```python
# In orchestrator.py - add snow data
snow_json = await fetch_snow(lat, lon, hours) if plan.get("need_snow") else None

# Extract snow arrays
snowfall = _get_hourly_array(snow_json, "snowfall") if snow_json else None
snow_depth = _get_hourly_array(snow_json, "snow_depth") if snow_json else None

# Compute
snowfall_sum = sum(s for s in (snowfall or []) if s is not None)
snow_depth_avg = safe_avg(snow_depth)
```

### 21.4) Update LLM prompts

**agent/prompts/guidance_user_template.txt** — add:
```txt
Snow conditions:
- Snowfall (next {hours}h): {snowfall_sum} cm
- Snow depth: {snow_depth_avg} cm
```

---

## 22) Feature B: Geocoding (Place Names → Coordinates) 📍

### 22.1) Get Google Maps API Key

1. Go to: https://console.cloud.google.com/
2. Create project or select existing
3. Enable "Geocoding API"
4. Create API Key
5. Add to `.env`:
   ```env
   GOOGLE_MAPS_API_KEY=your_key_here
   ```

### 22.2) Create geocoding tool

**agent/tools/google_geocoding.py**
```python
import os
from agent.retry import request_with_retry

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

async def geocode_place(place_name: str) -> dict:
    """
    Convert place name to coordinates using Google Geocoding API.
    
    Args:
        place_name: e.g., "Sofia, Bulgaria" or "Витоша"
    
    Returns:
        {
            "latitude": 42.6977,
            "longitude": 23.3219,
            "formatted_address": "Sofia, Bulgaria",
            "found": True
        }
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not configured")
    
    params = {
        "address": place_name,
        "key": api_key,
        "language": "bg"  # or "en" for English results
    }
    
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10.0"))
    data = await request_with_retry("GET", GEOCODE_URL, params=params, timeout=timeout)
    
    if data.get("status") != "OK" or not data.get("results"):
        return {
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "found": False,
            "error": data.get("status", "NO_RESULTS")
        }
    
    result = data["results"][0]
    location = result["geometry"]["location"]
    
    return {
        "latitude": location["lat"],
        "longitude": location["lng"],
        "formatted_address": result["formatted_address"],
        "found": True
    }
```

### 22.3) Add geocode endpoint

**service/schemas.py** — add:
```python
class GeocodeRequest(BaseModel):
    place_name: str = Field(..., description="Place name, e.g., 'Sofia' or 'Витоша'")

class GeocodeResponse(BaseModel):
    latitude: float | None
    longitude: float | None
    formatted_address: str | None
    found: bool
```

**service/routes.py** — add:
```python
from service.schemas import GeocodeRequest, GeocodeResponse
from agent.tools.google_geocoding import geocode_place

@router.post("/geocode", response_model=GeocodeResponse, tags=["Geocoding"])
async def geocode(req: GeocodeRequest):
    """
    Convert place name to coordinates.
    
    Example: "Sofia, Bulgaria" → { latitude: 42.6977, longitude: 23.3219 }
    """
    return await geocode_place(req.place_name)
```

### 22.4) Enhanced /analyze with place name

**service/schemas.py** — update AnalyzeRequest:
```python
class AnalyzeRequest(BaseModel):
    # Option 1: Direct coordinates
    latitude: float | None = Field(None, ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: float | None = Field(None, ge=-180, le=180, description="Longitude (-180 to 180)")
    
    # Option 2: Place name (will be geocoded)
    place_name: str | None = Field(None, description="Place name, e.g., 'Sofia' or 'Пловдив'")
    
    hours: int = Field(default=6, ge=1, le=168, description="Hours to analyze (1-168)")
    
    @model_validator(mode='after')
    def check_location(self):
        has_coords = self.latitude is not None and self.longitude is not None
        has_place = self.place_name is not None
        if not has_coords and not has_place:
            raise ValueError("Provide either (latitude, longitude) or place_name")
        return self
```

**agent/orchestrator.py** — update:
```python
async def analyze_air_and_weather(
    lat: float | None, 
    lon: float | None, 
    hours: int,
    place_name: str | None = None
):
    # If place_name provided, geocode it first
    if place_name and (lat is None or lon is None):
        geo = await geocode_place(place_name)
        if not geo["found"]:
            raise ValueError(f"Could not find location: {place_name}")
        lat = geo["latitude"]
        lon = geo["longitude"]
    
    validate_lat_lon(lat, lon)
    # ... rest of the flow
```

---

## 23) Feature C: Route Weather 🚗

### 23.1) Get Google Directions API

1. Enable "Directions API" in Google Cloud Console
2. Same API key can be used (or create separate)

### 23.2) Create directions tool

**agent/tools/google_directions.py**
```python
import os
from agent.retry import request_with_retry

DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"

async def get_route_waypoints(origin: str, destination: str, num_points: int = 5) -> list[dict]:
    """
    Get waypoints along a driving route.
    
    Args:
        origin: Starting point, e.g., "Sofia, Bulgaria"
        destination: End point, e.g., "Plovdiv, Bulgaria"
        num_points: Number of waypoints to sample (default 5)
    
    Returns:
        List of waypoints with coordinates and estimated time:
        [
            {"lat": 42.6977, "lng": 23.3219, "eta_minutes": 0, "location": "Sofia"},
            {"lat": 42.4502, "lng": 24.7520, "eta_minutes": 75, "location": "On route"},
            {"lat": 42.1350, "lng": 24.7453, "eta_minutes": 150, "location": "Plovdiv"}
        ]
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not configured")
    
    params = {
        "origin": origin,
        "destination": destination,
        "mode": "driving",
        "key": api_key,
        "language": "bg"
    }
    
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10.0"))
    data = await request_with_retry("GET", DIRECTIONS_URL, params=params, timeout=timeout)
    
    if data.get("status") != "OK" or not data.get("routes"):
        return []
    
    route = data["routes"][0]
    legs = route["legs"][0]
    steps = legs["steps"]
    
    # Sample waypoints evenly along the route
    waypoints = []
    total_duration = legs["duration"]["value"]  # seconds
    
    # Start point
    waypoints.append({
        "lat": legs["start_location"]["lat"],
        "lng": legs["start_location"]["lng"],
        "eta_minutes": 0,
        "location": legs["start_address"]
    })
    
    # Intermediate points
    accumulated_duration = 0
    interval = total_duration / (num_points - 1) if num_points > 1 else total_duration
    
    for step in steps:
        accumulated_duration += step["duration"]["value"]
        # Check if we've passed an interval
        if accumulated_duration >= interval * len(waypoints) and len(waypoints) < num_points - 1:
            waypoints.append({
                "lat": step["end_location"]["lat"],
                "lng": step["end_location"]["lng"],
                "eta_minutes": round(accumulated_duration / 60),
                "location": "On route"
            })
    
    # End point
    waypoints.append({
        "lat": legs["end_location"]["lat"],
        "lng": legs["end_location"]["lng"],
        "eta_minutes": round(total_duration / 60),
        "location": legs["end_address"]
    })
    
    return waypoints
```

### 23.3) Add route weather endpoint

**service/schemas.py** — add:
```python
class RouteWeatherRequest(BaseModel):
    origin: str = Field(..., description="Starting point, e.g., 'Sofia'")
    destination: str = Field(..., description="End point, e.g., 'Plovdiv'")
    departure_hours_from_now: int = Field(default=0, ge=0, le=168, 
        description="When to depart (0 = now)")

class WaypointWeather(BaseModel):
    location: str
    eta_minutes: int
    latitude: float
    longitude: float
    temperature: float | None
    pm25: float | None
    snowfall: float | None
    snow_depth: float | None
    conditions: str  # "Clear", "Snow expected", etc.

class RouteWeatherResponse(BaseModel):
    origin: str
    destination: str
    total_duration_minutes: int
    waypoints: list[WaypointWeather]
    summary: str  # AI-generated summary
    warnings: list[str]  # e.g., ["Heavy snow expected near Plovdiv"]
```

**service/routes.py** — add:
```python
from service.schemas import RouteWeatherRequest, RouteWeatherResponse
from agent.orchestrator import analyze_route_weather

@router.post("/route-weather", response_model=RouteWeatherResponse, tags=["Route"])
async def route_weather(req: RouteWeatherRequest):
    """
    Get weather forecast along a driving route.
    
    Use case: "What's the weather on my trip from Sofia to Plovdiv?"
    
    Returns weather conditions at multiple waypoints along the route,
    with AI-generated summary and warnings.
    """
    return await analyze_route_weather(
        origin=req.origin,
        destination=req.destination,
        departure_hours=req.departure_hours_from_now
    )
```

### 23.4) Implement route weather orchestrator

**agent/orchestrator.py** — add:
```python
from agent.tools.google_directions import get_route_waypoints
from agent.tools.open_meteo import fetch_weather, fetch_air_quality, fetch_snow

async def analyze_route_weather(origin: str, destination: str, departure_hours: int = 0):
    """
    Get weather for each waypoint along a route.
    """
    # 1. Get route waypoints
    waypoints = await get_route_waypoints(origin, destination, num_points=5)
    if not waypoints:
        raise ValueError(f"Could not find route from {origin} to {destination}")
    
    # 2. Fetch weather for each waypoint (in parallel)
    import asyncio
    
    async def get_waypoint_weather(wp: dict, departure_hours: int):
        lat, lon = wp["lat"], wp["lng"]
        # Calculate forecast hour based on ETA
        forecast_hour = departure_hours + (wp["eta_minutes"] // 60)
        
        # Fetch data (just 1 hour for this specific time)
        wx = await fetch_weather(lat, lon, hours=forecast_hour + 1)
        air = await fetch_air_quality(lat, lon, hours=forecast_hour + 1)
        snow = await fetch_snow(lat, lon, hours=forecast_hour + 1)
        
        # Extract values at the forecast hour
        temp = wx.get("hourly", {}).get("temperature_2m", [None])[forecast_hour] if wx else None
        pm25 = air.get("hourly", {}).get("pm2_5", [None])[forecast_hour] if air else None
        snowfall = snow.get("hourly", {}).get("snowfall", [None])[forecast_hour] if snow else None
        snow_depth = snow.get("hourly", {}).get("snow_depth", [None])[forecast_hour] if snow else None
        
        # Determine conditions
        conditions = "Clear"
        if snowfall and snowfall > 0:
            conditions = "Snow expected"
        if snowfall and snowfall > 1:
            conditions = "Heavy snow"
        
        return {
            "location": wp["location"],
            "eta_minutes": wp["eta_minutes"],
            "latitude": lat,
            "longitude": lon,
            "temperature": round(temp, 1) if temp else None,
            "pm25": round(pm25, 1) if pm25 else None,
            "snowfall": round(snowfall, 1) if snowfall else None,
            "snow_depth": round(snow_depth, 1) if snow_depth else None,
            "conditions": conditions
        }
    
    # Fetch all in parallel
    tasks = [get_waypoint_weather(wp, departure_hours) for wp in waypoints]
    waypoint_weather = await asyncio.gather(*tasks)
    
    # 3. Generate warnings
    warnings = []
    for wp in waypoint_weather:
        if wp["snowfall"] and wp["snowfall"] > 0.5:
            warnings.append(f"Snow expected near {wp['location']} ({wp['snowfall']} cm)")
        if wp["temperature"] and wp["temperature"] < 0:
            warnings.append(f"Below freezing at {wp['location']} ({wp['temperature']}°C)")
        if wp["pm25"] and wp["pm25"] > 50:
            warnings.append(f"Poor air quality at {wp['location']} (PM2.5: {wp['pm25']})")
    
    # 4. Generate AI summary
    summary = await generate_route_summary(waypoint_weather, origin, destination)
    
    return {
        "origin": origin,
        "destination": destination,
        "total_duration_minutes": waypoints[-1]["eta_minutes"] if waypoints else 0,
        "waypoints": waypoint_weather,
        "summary": summary,
        "warnings": warnings
    }

async def generate_route_summary(waypoints: list, origin: str, destination: str) -> str:
    """Generate AI summary for route weather."""
    # Build context for LLM
    from agent.tools.github_models_llm import generate_guidance_text
    from agent.validate import QualityFlags
    
    # Simple summary generation (or use LLM)
    temps = [wp["temperature"] for wp in waypoints if wp["temperature"]]
    snow_total = sum(wp["snowfall"] or 0 for wp in waypoints)
    
    if not temps:
        return f"Weather data unavailable for route {origin} → {destination}."
    
    min_temp = min(temps)
    max_temp = max(temps)
    
    summary = f"Route: {origin} → {destination}. "
    summary += f"Temperature range: {min_temp}°C to {max_temp}°C. "
    
    if snow_total > 0:
        summary += f"Expected snowfall along route: {snow_total:.1f} cm. Drive carefully! "
    else:
        summary += "No snow expected. "
    
    if min_temp < 0:
        summary += "⚠️ Watch for icy roads. "
    
    return summary + "\n\nWeather data by Open-Meteo.com"
```

---

## 24) Update .env.example for Phase 2

**.env.example** — add:
```env
# Phase 1 (existing)
GITHUB_MODELS_TOKEN=replace_me
GITHUB_MODELS_MODEL=gpt-4o-mini
NASA_API_KEY=DEMO_KEY
CACHE_TTL_SECONDS=600
HTTP_TIMEOUT_SECONDS=10.0
LLM_TIMEOUT_SECONDS=15.0

# Phase 2 (new)
GOOGLE_MAPS_API_KEY=replace_me
```

---

## 25) Update Copilot Studio with new tools

After implementing Phase 2:

1. **Regenerate OpenAPI**
   ```bash
   curl -s http://localhost:8000/openapi.json > service/openapi.json
   ```

2. **Re-import in Copilot Studio**
   - Delete old tool
   - Import new `openapi.json`
   - Configure new endpoints:
     - `/geocode` - "Use when user mentions a place name"
     - `/route-weather` - "Use when user asks about trip/route weather"

3. **Update Copilot instructions**
   ```
   You are OutdoorMate, an outdoor activity assistant.
   
   Available tools:
   1. analyze - Air quality, weather, snow for a location
   2. geocode - Convert place name to coordinates
   3. route-weather - Weather forecast along a driving route
   
   When user mentions a place by name (like "Sofia"), use geocode first,
   then use analyze with the coordinates.
   
   When user asks about a trip (A to B), use route-weather.
   ```

---

## Phase 2 Implementation Order

| Step | Feature | Priority | Dependency |
|------|---------|----------|------------|
| 21 | Snow data | High | None |
| 22 | Geocoding | High | Google API key |
| 23 | Route weather | Medium | Steps 21, 22 |
| 24 | Update .env | High | - |
| 25 | Update Copilot Studio | High | Steps 21-24 |

**Estimated effort**: 4-6 hours total
