# Technical Execution Steps (EN) — Air & Insights Copilot

This file is a **hands-on runbook**: exactly what to do, where, and how to implement the project.  
Target: **Track B first** (FastAPI + minimal web UI/CLI), keeping the same **OpenAPI contract** for later Copilot Studio wiring.

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
