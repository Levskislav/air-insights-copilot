# Air & Insights Copilot — README (BG)

## Какво е това?
Услуга (FastAPI) + agent orchestration, която:
- взима PM2.5/PM10 (Open-Meteo Air Quality) и температура (Open-Meteo Forecast)
- изчислява средни за следващите N часа
- генерира guidance текст чрез GitHub Models (free inference)
- (по избор) връща NASA APOD за днес

## Стартиране локално

### 1) Инсталация
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Конфигурация
Копирай `.env.example` → `.env` и попълни:
- `GITHUB_MODELS_TOKEN`
- `GITHUB_MODELS_MODEL`
(по избор) `NASA_API_KEY=DEMO_KEY`

### 3) Run
```bash
uvicorn service.main:app --reload --port 8000
```

Swagger:
- http://localhost:8000/docs

## Демонстрационни заявки

### Analyze
```bash
curl -s -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"latitude":42.6977,"longitude":23.3219,"hours":6}'
```

### APOD (optional)
```bash
curl -s http://localhost:8000/apod/today
```

## Attribution
Отговорите трябва да включват:
`Weather data by Open-Meteo.com`

## Copilot Studio интеграция (Track A)
1) Deploy-вай service-а на публичен HTTPS URL
2) Export OpenAPI:
```bash
curl -s https://<your-host>/openapi.json > service/openapi.json
```
3) Import OpenAPI в Copilot Studio като REST Tool/Action
4) Включи Generative Orchestration
5) Тествай с демо prompt-овете
