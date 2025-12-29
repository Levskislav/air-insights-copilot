# OutdoorMate

**Intelligent Outdoor Activity Assistant** — AI-powered weather, air quality, and route analysis.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-52%20passing-brightgreen.svg)]()


---

## Features

| Feature | Description |
|---------|-------------|
| **Weather Forecast** | Temperature, rain, visibility, wind, cloud cover |
| **Air Quality** | PM2.5 and PM10 pollution levels |
| **Snow Conditions** | Snowfall and snow depth for winter activities |
| **Geocoding** | Convert place names to coordinates ("Sofia" -> lat/lon) |
| **AI Guidance** | Personalized recommendations via GitHub Models LLM |
| **Teams Integration** | Microsoft Teams Message Extension |

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
|  |          | |          | |          | |               |   |
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
|  |   Snow     | |            | |            | |          |  |
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
- **67 tests passing**
- Unit tests for validation and computation
- Integration tests with mocked APIs
- Security tests (injection prevention, input validation, error handling)

---

## Copilot Studio Integration

> **Note:** Copilot Studio requires a **public URL** - it cannot connect to localhost.

### Step 1: Deploy to GitHub Codespaces

1. Open repo in GitHub → **Code** → **Codespaces** → **Create codespace**
2. Run: `uvicorn service.main:app --host 0.0.0.0 --port 8000`
3. In **Ports** tab → Make port 8000 **Public**
4. Copy the public URL (e.g., `https://xxx-8000.app.github.dev`)

> **For Teams Integration:** Also make port **3978** public and run `cd teams_integration && npm install && npm run dev`

### Step 2: Create REST API Tools in Copilot Studio

1. Go to [Copilot Studio](https://copilotstudio.microsoft.com)
2. Create Agent → Tools → **+ Add a tool**
3. Select **REST API**
4. Upload OpenAPI files (repeat for each):

| OpenAPI File | Tool Name | Description |
|--------------|-----------|-------------|
| `service/openapi_simple.json` | Weather for Place | Weather by city/place name |
| `service/openapi_coords.json` | Weather for Coordinates | Weather by GPS coordinates |
| `service/openapi_apod.json` | NASA APOD API | Astronomy Picture of the Day |

5. Follow wizard: Next → Next → **Publish**
6. Configure: Set "After running" to **"Write the response with generative AI"**

### Step 3: Test

Ask: "What's the weather in Sofia?"

See `docs/copilot_tool_snippet.md` for detailed tool descriptions.

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
│       ├── github_models_llm.py
│       └── nasa_apod.py
├── service/                  # FastAPI application
│   ├── main.py               # App entry point
│   ├── routes.py             # HTTP endpoints
│   ├── schemas.py            # Pydantic models
│   └── openapi_*.json        # OpenAPI specs for Copilot Studio
├── teams_integration/        # Teams Message Extension
│   ├── src/                  # TypeScript source
│   ├── appPackage/           # Teams app manifest
│   └── package.json          # Node.js dependencies
├── tests/                    # Test suite
├── docs/                     # Documentation
├── .devcontainer/            # GitHub Codespaces config
├── .env.example              # Environment template
├── start.sh                  # Start all services
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_MODELS_TOKEN` | Yes | GitHub PAT for LLM access |
| `GOOGLE_MAPS_API_KEY` | Yes | For geocoding (place name to coordinates) |
| `NASA_API_KEY` | No | For APOD (default: DEMO_KEY) |
| `CACHE_TTL_SECONDS` | No | Cache duration (default: 600) |

---

## Demonstration Prompts

Test the system with these example prompts:

1. **Air quality check:**
   > "Is the air quality good for jogging in Plovdiv?"

2. **Weather with coordinates:**
   > "What's the PM2.5 and temperature around 42.6977, 23.3219 for the next 6 hours?"

3. **Snow conditions:**
   > "Is there snow in Bansko? Can I go skiing this weekend?"

4. **NASA APOD:**
   > "What's the astronomy picture of the day?"

---

## Quality Gates

| Requirement | Status |
|-------------|--------|
| Lat/lon bounds validation (-90 to 90, -180 to 180) | ✅ Done |
| Hours range [1..72] | ✅ Done |
| Attribution in responses | ✅ Done |
| Request logging | ✅ Done |
| Retry with exponential backoff | ✅ Done |
| 10-minute caching | ✅ Done |

---

## Attribution

- Weather data by [Open-Meteo.com](https://open-meteo.com/)
- LLM by [GitHub Models](https://github.com/marketplace/models)
- Maps by [Google Maps Platform](https://developers.google.com/maps)
- APOD by [NASA](https://api.nasa.gov/)

---

## Author

**Dimitar Todorov** - [GitHub](https://github.com/Levskislav)
