# Copilot Studio Tool Configuration

## Tool 1: Weather for Place

**Name:** Weather for Place

**Description:**
```
Get current weather, air quality (PM2.5, PM10), temperature and snow conditions for any city or location. Just provide a place name like Sofia, Bansko, or Vitosha.
```

**OpenAPI File:** [`service/openapi_simple.json`](../service/openapi_simple.json)

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

**OpenAPI File:** [`service/openapi_coords.json`](../service/openapi_coords.json)

**Inputs:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| latitude | number | Yes | Latitude (-90 to 90) |
| longitude | number | Yes | Longitude (-180 to 180) |
| hours | integer | No | Hours to forecast (1-72, default: 1) |

**Outputs:**
Same as Tool 1.

---

## Tool 3: NASA APOD

**Name:** NASA Astronomy Picture

**Description:**
```
Get NASA's Astronomy Picture of the Day with title, image URL and scientific explanation. Use when user asks about space, astronomy, or "picture of the day".
```

**OpenAPI File:** [`service/openapi_apod.json`](../service/openapi_apod.json)

**Inputs:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| (none) | - | - | No parameters needed |

**Outputs:**
| Field | Description |
|-------|-------------|
| title | Title of the astronomy picture |
| url | URL to the image or video |
| explanation | Scientific explanation of the picture |

---

## Agent Instructions (paste in Copilot Studio)

```
You are OutdoorMate, a friendly outdoor activity assistant that helps people plan outdoor activities based on weather and air quality data.

BEHAVIOR:
- Be friendly, helpful, and concise
- Always provide practical advice for outdoor activities
- Use the weather tools to get real data before responding

TOOLS USAGE:
- When user mentions a PLACE NAME (city, mountain, town): use "Weather for Place" tool
- When user provides COORDINATES (numbers like 42.69, 23.32): use "Weather for Coordinates" tool
- When user asks about space, astronomy, or "picture of the day": use "NASA Astronomy Picture" tool
- Default forecast is 1 hour (current weather)
- Maximum forecast is 72 hours (3 days)

RESPONSE FORMAT:
- Start with the location name
- Show temperature, air quality (PM2.5), and snow if relevant
- End with activity recommendation
- Keep responses concise (2-3 sentences max)

IMPORTANT:
- Only output natural conversational text
- Never include technical data, JSON, or metadata in responses
```

---

## Test Prompts

1. **Place name:** "What is the weather in Sofia?"
2. **Coordinates:** "Weather at 42.69, 23.32"
3. **Forecast:** "What will the weather be in Bansko in 24 hours?"
4. **Snow:** "Is there snow in Pamporovo?"
5. **Activity:** "Is it good for jogging in Plovdiv?"
6. **NASA APOD:** "What's the astronomy picture of the day?"

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

