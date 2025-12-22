# Copilot Studio Tool Snippet (EN) — Air & Insights Copilot

Use this snippet when adding your REST API as a Tool/Action in Copilot Studio (Generative Orchestration ON).

## Tool name
`analyzeAirAndWeather`

## When to use
Use this tool when the user asks about any of:
- air quality (PM2.5, PM10), pollution, breathing comfort
- weather temperature in the next hours
- “Is it safe to run outdoors?” or similar outdoor activity decisions
- location given as latitude/longitude

## Endpoints
### POST /analyze
**Input**
```json
{ "latitude": 42.6977, "longitude": 23.3219, "hours": 6 }
```

**Output**
```json
{
  "pm25_avg": 12.3,
  "pm10_avg": 18.1,
  "temp_avg": 6.7,
  "guidance_text": "..."
}
```

### GET /apod/today (optional)
Returns NASA Astronomy Picture of the Day.

## Notes for orchestration
- If the user asks “today’s APOD”, call `/apod/today`.
- Otherwise, if question includes PM/air/temperature/outdoors safety, call `/analyze`.

## Attribution requirement
Make sure responses include:
`Weather data by Open-Meteo.com`
