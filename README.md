# OutdoorMate

**Intelligent Outdoor Activity Assistant** — AI-powered weather, air quality, and route analysis.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-38%20passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

| Feature | Description |
|---------|-------------|
| **Weather Forecast** | Temperature, rain, visibility, wind, cloud cover |
| **Air Quality** | PM2.5 and PM10 pollution levels |
| **Snow Conditions** | Snowfall and snow depth for winter activities |
| **Geocoding** | Convert place names to coordinates ("Sofia" -> lat/lon) |
| **Route Weather** | Full road conditions along driving route A -> B |
| **AI Guidance** | Personalized recommendations via GitHub Models LLM |

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
|  | /analyze | | /geocode | |  /route  | |  /apod/today  |   |
|  |          | |          | | -weather | |               |   |
|  +----+-----+ +----+-----+ +----+-----+ +---------------+   |
+-------+------------+------------+---------------------------+
        |            |            |
        v            v            v
+-------------------------------------------------------------+
|                     Agent Orchestrator                      |
|  +--------+ +--------+ +---------+ +--------+ +---------+   |
|  |Planner | |Validate| | Compute | | Cache  | |   LLM   |   |
|  +--------+ +--------+ +---------+ +--------+ +---------+   |
+-------+------------+------------+---------------------------+
        |            |            |
        v            v            v
+-------------------------------------------------------------+
|                      External APIs                          |
|  +------------+ +------------+ +------------+ +----------+  |
|  | Open-Meteo | |  Google    | |  GitHub    | |   NASA   |  |
|  |  Weather   | |   Maps     | |  Models    | |   APOD   |  |
|  | Air Quality| | Geocoding  | |   (LLM)    | |          |  |
|  |   Snow     | | Directions | |            | |          |  |
|  +------------+ +------------+ +------------+ +----------+  |
+-------------------------------------------------------------+
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Levskislav/air-insights-copilot.git
cd air-insights-copilot
```

### 2. Create virtual environment

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create a `.env` file:

```env
# GitHub Models (LLM) - Required
GITHUB_MODELS_TOKEN=your_github_pat

# Google Maps API - Required for geocoding/routes
GOOGLE_MAPS_API_KEY=your_google_api_key

# NASA APOD - Optional
NASA_API_KEY=DEMO_KEY
```

### 5. Run the server

```bash
uvicorn service.main:app --reload --port 8000
```

### 6. Open Swagger UI

Visit: http://localhost:8000/docs

---

## API Endpoints

### POST /analyze

Analyze air quality and weather for a location.

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"latitude": 42.6977, "longitude": 23.3219, "hours": 6}'
```

Or with place name:

```bash
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

Convert place name to coordinates.

```bash
curl -X POST http://localhost:8000/geocode \
  -H "Content-Type: application/json" \
  -d '{"place_name": "Vitosha mountain"}'
```

### POST /route-weather

Get weather conditions along a driving route.

```bash
curl -X POST http://localhost:8000/route-weather \
  -H "Content-Type: application/json" \
  -d '{"origin": "Sofia", "destination": "Plovdiv"}'
```

### GET /apod/today

Get NASA Astronomy Picture of the Day.

```bash
curl http://localhost:8000/apod/today
```

---

## Testing

Run all tests:

```bash
pytest tests/ -v
```

Current test coverage:
- **38 tests passing**
- Unit tests for validation and computation
- Integration tests with mocked APIs

---

## Copilot Studio Integration

1. Deploy API to GitHub Codespaces (public URL)
2. Export OpenAPI spec: `GET /openapi.json`
3. Import into Power Automate as Custom Connector
4. Add connector actions to Copilot Studio

See `docs/copilot_tool_snippet.md` for detailed instructions.

---

## Project Structure

```
air_insights/
├── agent/                    # Core agent logic
│   ├── orchestrator.py       # Main coordination
│   ├── planner.py            # Execution planning
│   ├── validate.py           # Input validation
│   ├── compute.py            # Statistical functions
│   ├── cache.py              # TTL caching
│   ├── retry.py              # Resilient HTTP calls
│   ├── prompts/              # LLM prompts
│   └── tools/                # External API integrations
│       ├── open_meteo.py     # Weather & air quality
│       ├── google_geocoding.py
│       ├── google_directions.py
│       ├── github_models_llm.py
│       └── nasa_apod.py
├── service/                  # FastAPI application
│   ├── main.py               # App entry point
│   ├── routes.py             # HTTP endpoints
│   └── schemas.py            # Pydantic models
├── tests/                    # Test suite
│   ├── test_compute.py
│   ├── test_validate.py
│   └── test_integration_analyze.py
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_MODELS_TOKEN` | Yes | GitHub PAT for LLM access |
| `GOOGLE_MAPS_API_KEY` | Yes | For geocoding and directions |
| `NASA_API_KEY` | No | For APOD (default: DEMO_KEY) |
| `CACHE_TTL_SECONDS` | No | Cache duration (default: 600) |

---

## Attribution

- Weather data by [Open-Meteo.com](https://open-meteo.com/)
- LLM by [GitHub Models](https://github.com/marketplace/models)
- Maps by [Google Maps Platform](https://developers.google.com/maps)
- APOD by [NASA](https://api.nasa.gov/)

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

## Author

**Levskislav** - [GitHub](https://github.com/Levskislav)
