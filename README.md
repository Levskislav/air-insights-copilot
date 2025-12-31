# OutdoorMate

**Intelligent Outdoor Activity Assistant** — AI-powered weather, air quality, and snow analysis with personalized guidance.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-89%20passing-brightgreen.svg)]()

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Testing](#testing)
- [Copilot Studio Integration](#copilot-studio-integration)
- [Project Structure](#project-structure)
- [Attribution](#attribution)

---

## Features

| Feature | Description |
|---------|-------------|
| **Weather Forecast** | Temperature, rain, visibility, wind, cloud cover |
| **Air Quality** | PM2.5 and PM10 pollution levels |
| **Snow Conditions** | Snowfall and snow depth for winter activities |
| **Geocoding** | Convert place names to coordinates ("Sofia" → lat/lon) |
| **AI Guidance** | Personalized recommendations via GitHub Models LLM |
| **Teams Integration** | Microsoft Teams Message Extension |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Levskislav/air-insights-copilot.git
cd air-insights-copilot

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\Activate.ps1     # Windows

# 3. Install
pip install -r requirements.txt

# 4. Configure (.env file)
GITHUB_MODELS_TOKEN=your_github_pat
GOOGLE_MAPS_API_KEY=your_google_api_key
NASA_API_KEY=DEMO_KEY

# 5. Run
uvicorn service.main:app --reload --port 8000

# 6. Open Swagger UI
# http://localhost:8000/docs
```

---

## API Endpoints

### POST /analyze

Analyze air quality and weather for a location.

```bash
# With coordinates
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"latitude": 42.6977, "longitude": 23.3219, "hours": 6}'

# With place name
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"place_name": "Sofia", "hours": 6}'
```

**Response:**
```json
{
  "pm25_avg": 28.5,
  "pm10_avg": 35.2,
  "temp_avg": 15.3,
  "snowfall_sum": 0.0,
  "snow_depth_avg": 5.0,
  "guidance_text": "Air quality is moderate..."
}
```

### POST /geocode

```bash
curl -X POST http://localhost:8000/geocode \
  -H "Content-Type: application/json" \
  -d '{"place_name": "Vitosha mountain"}'
```

### GET /apod/today

```bash
curl http://localhost:8000/apod/today
```

### GET /health

```bash
curl http://localhost:8000/health
```

---

## Architecture

```
+-------------------------------------------------------------+
|                    COPILOT STUDIO                           |
|                   (OutdoorMate Agent)                       |
+---------------------------+---------------------------------+
                            | OpenAPI 3.0
                            v
+-------------------------------------------------------------+
|                     FastAPI Service                         |
|  +----------+ +----------+ +----------+ +---------------+   |
|  | /analyze | | /geocode | | /health  | |  /apod/today  |   |
|  +----------+ +----------+ +----------+ +---------------+   |
+-------------------------------------------------------------+
                            |
                            v
+-------------------------------------------------------------+
|                     Agent Orchestrator                      |
|  +--------+ +--------+ +---------+ +--------+ +---------+   |
|  |Planner | |Validate| | Compute | | Cache  | |   LLM   |   |
|  +--------+ +--------+ +---------+ +--------+ +---------+   |
|  +----------------+ +-------------------+ +-------------+   |
|  |Circuit Breaker | | Shared HTTP Client| | Retry Logic |   |
|  +----------------+ +-------------------+ +-------------+   |
+-------------------------------------------------------------+
                            |
                            v
+-------------------------------------------------------------+
|                      External APIs                          |
|  +------------+ +------------+ +------------+ +----------+  |
|  | Open-Meteo | |  Google    | |  GitHub    | |   NASA   |  |
|  |  Weather   | |   Maps     | |  Models    | |   APOD   |  |
|  +------------+ +------------+ +------------+ +----------+  |
+-------------------------------------------------------------+
```

---

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_MODELS_TOKEN` | Yes | GitHub PAT for LLM access |
| `GOOGLE_MAPS_API_KEY` | Yes | For geocoding |
| `NASA_API_KEY` | No | For APOD (default: DEMO_KEY) |
| `CACHE_TTL_SECONDS` | No | Cache duration (default: 600) |

> **Note:** Legacy variable names (`GITHUB_TOKEN`, `GOOGLE_API_KEY`) are also supported for backwards compatibility.

---

## Testing

```bash
pytest tests/ -v
```

**89 tests** covering validation, computation, caching, retry, integration, and security.

| Category | Tests | Description |
|----------|-------|-------------|
| Validation | 18 | Input validation and data quality |
| Computation | 10 | Statistical functions |
| Cache | 12 | Thread-safe caching |
| Retry | 10 | HTTP retry with circuit breaker |
| Integration | 7 | API endpoint tests |
| Security | 16 | DAST + SAST |

📄 See [docs/TESTING.md](docs/TESTING.md) for detailed test descriptions.

---

## Copilot Studio Integration

> **Requires a public URL** 

### Deploy to Codespaces

1. Open repo → **Code** → **Codespaces** → **Create codespace**
2. Run: `uvicorn service.main:app --host 0.0.0.0 --port 8000`
3. **Ports** tab → Make port 8000 **Public**
4. Copy URL: `https://xxx-8000.app.github.dev`

### Add Tools in Copilot Studio

1. [Copilot Studio](https://copilotstudio.microsoft.com) → Create Agent → Tools → **+ Add tool**
2. Select **REST API** → Upload OpenAPI files:

| File | Tool Name |
|------|-----------|
| `service/openapi_simple.json` | Weather for Place |
| `service/openapi_coords.json` | Weather for Coordinates |
| `service/openapi_apod.json` | NASA APOD |

3. Set "After running" to **"Write response with generative AI"**

### Test Prompts

- "What's the weather in Sofia?"
- "Is the air quality good for jogging in Plovdiv?"
- "Is there snow in Bansko? Can I go skiing?"
- "What's the astronomy picture of the day?"

---

## Project Structure

```
air_insights/
├── agent/                    # Core agent logic
│   ├── orchestrator.py       # Main coordination
│   ├── planner.py            # Execution planning
│   ├── validate.py           # Input validation
│   ├── compute.py            # Statistical functions
│   ├── cache.py              # Thread-safe TTL caching
│   ├── retry.py              # Resilient HTTP calls
│   ├── circuit_breaker.py    # Circuit breaker pattern
│   ├── http_client.py        # Shared HTTP client
│   └── tools/                # External API integrations
├── service/                  # FastAPI application
│   ├── main.py               # App entry point
│   ├── routes.py             # HTTP endpoints
│   ├── schemas.py            # Pydantic models
│   └── openapi_*.json        # OpenAPI specs
├── teams_integration/        # Teams Message Extension
├── tests/                    # Test suite (89 tests)
├── docs/                     # Documentation
└── requirements.txt          # Python dependencies
```

---

## Attribution

- Weather data by [Open-Meteo.com](https://open-meteo.com/)
- LLM by [GitHub Models](https://github.com/marketplace/models)
- Maps by [Google Maps Platform](https://developers.google.com/maps)
- APOD by [NASA](https://api.nasa.gov/)

---

**Author:** [Dimitar Todorov](https://github.com/Levskislav)
