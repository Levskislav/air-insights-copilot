# Copilot Studio Tool Configuration

## Tool 1: Weather for Place

**Name:** Weather for Place

**Description:**
```
Get current weather, air quality (PM2.5, PM10), temperature and snow conditions for any city or location. Just provide a place name like Sofia, Bansko, or Vitosha.
```

**OpenAPI File:** `service/openapi_simple.json`

**Inputs:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| place_name | string | Yes | Name of the place (city, town, mountain) |
| hours | integer | No | Hours to forecast (1-72, default: 1) |

**Outputs:**
| Field | Description |
|-------|-------------|
| pm25_avg | PM2.5 air quality level (μg/m³) |
| pm10_avg | PM10 air quality level (μg/m³) |
| temp_avg | Temperature in Celsius |
| snowfall_sum | Total snowfall in cm |
| snow_depth_avg | Snow depth on ground in cm |
| guidance_text | AI-generated weather guidance |

---

## Tool 2: Weather for Coordinates

**Name:** Weather for Coordinates

**Description:**
```
Get weather, air quality and snow data using GPS coordinates. Use when user provides numbers like 42.69, 23.32 or says "coordinates".
```

**OpenAPI File:** `service/openapi_coords.json`

**Inputs:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| latitude | number | Yes | Latitude (-90 to 90) |
| longitude | number | Yes | Longitude (-180 to 180) |
| hours | integer | No | Hours to forecast (1-72, default: 1) |

**Outputs:**
Same as Tool 1.

---

## Agent Instructions (paste in Copilot Studio)

```
You are OutdoorMate, a friendly outdoor activity assistant.

RULES:
1. When user asks about weather for a PLACE NAME (city, town, mountain), use "Weather for Place" tool
2. When user provides COORDINATES (numbers like 42.69, 23.32), use "Weather for coordinates" tool
3. Default hours is 1 (current weather). Only ask for hours if user mentions a specific time period
4. Maximum forecast is 72 hours (3 days). If user asks for more, explain the limit
5. Always include air quality, temperature, and snow data in your response
6. Give practical advice for outdoor activities based on the data

RESPONSE FORMAT:
- Start with location and time period
- Show key metrics (temperature, air quality, snow)
- End with activity recommendation
```

---

## Test Prompts

1. **Place name:** "What is the weather in Sofia?"
2. **Coordinates:** "Weather at 42.69, 23.32"
3. **Forecast:** "What will the weather be in Bansko in 24 hours?"
4. **Snow:** "Is there snow in Pamporovo?"
5. **Activity:** "Is it good for jogging in Plovdiv?"

---

## Server URL

Update in OpenAPI files before importing:
```
https://YOUR-CODESPACE-URL-8000.app.github.dev
```

Example:
```
https://humble-winner-g7wwrw4rp9rcxvq-8000.app.github.dev
```

