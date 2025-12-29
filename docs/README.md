# OutdoorMate - Setup & Integration Guide

## Quick Setup

### 1. Clone & Install

```bash
git clone https://github.com/Levskislav/air-insights-copilot.git
cd air-insights-copilot
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
GITHUB_MODELS_TOKEN=your_github_pat
GOOGLE_MAPS_API_KEY=your_google_key
NASA_API_KEY=DEMO_KEY
```

### 3. Run Server

```bash
uvicorn service.main:app --reload --port 8000
```

### 4. Test

```bash
pytest tests/ -v
```

---

## API Contract

### POST /analyze

Request:
```json
{
  "latitude": 42.6977,
  "longitude": 23.3219,
  "hours": 6
}
```

Or with place name:
```json
{
  "place_name": "Sofia",
  "hours": 6
}
```

Response:
```json
{
  "pm25_avg": 28.5,
  "pm10_avg": 35.2,
  "temp_avg": 15.3,
  "snowfall_sum": 0.0,
  "snow_depth_avg": 5.0,
  "guidance_text": "Air quality is moderate. PM2.5 is 28.5 ug/m3..."
}
```

### GET /apod/today

Response:
```json
{
  "title": "Sunset over Earth",
  "url": "https://apod.nasa.gov/...",
  "explanation": "A beautiful sunset..."
}
```

---

## Copilot Studio Integration (Track A)

### Step 1: Deploy to GitHub Codespaces

1. Open repo in GitHub
2. Code -> Codespaces -> Create
3. Run: `uvicorn service.main:app --host 0.0.0.0 --port 8000`
4. Ports tab -> Make port 8000 **Public**
5. Copy the public URL

### Step 2: Create REST API Tool

1. Go to [Copilot Studio](https://copilotstudio.microsoft.com)
2. Create Agent -> Tools -> **+ Add a tool**
3. Select **REST API**
4. Upload `service/openapi_simple.json`
5. Follow wizard: Next -> Next -> **Publish**
6. Configure: Set "After running" to **"Write the response with generative AI"**

### Step 3: Test

Ask: "What's the weather in Sofia?"

---

## Demonstration Prompts

1. **Air quality check:**
   > "What's the PM2.5 and temperature around 42.6977, 23.3219 for the next 6 hours and should I run outdoors?"

2. **NASA APOD:**
   > "Show today's NASA APOD and summarize in 2 lines."

3. **Place name:**
   > "How's the air quality in Plovdiv?"

---

## Attribution

**Weather data by [Open-Meteo.com](https://open-meteo.com/)**

---

## Quality Gates

| Requirement | Status |
|------------|--------|
| Lat/lon bounds validation | Done |
| Hours range [1..72] | Done |
| Attribution in responses | Done |
| Request logging | Done |
| Retry with backoff | Done |
| 10-minute caching | Done |
