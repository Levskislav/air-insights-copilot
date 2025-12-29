# Teams Integration - OutdoorMate Message Extension

Teams Message Extension that integrates OutdoorMate weather API with Microsoft Teams and Microsoft 365 Copilot.

## Features

- 🌡️ **Weather Data** - Temperature, conditions
- 💨 **Air Quality** - PM2.5 and PM10 levels with health indicators
- ❄️ **Snow Conditions** - Snowfall and snow depth
- 🤖 **AI Guidance** - Personalized activity recommendations
- 🔌 **Copilot Plugin** - Works as Microsoft 365 Copilot plugin

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Microsoft Teams / Copilot                   │
│                              │                                  │
│                              ▼                                  │
│                    Bot Framework Service                        │
│                              │                                  │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Codespaces                           │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │  Teams Bot (3978)   │───▶│  OutdoorMate API (8000)         │ │
│  │  Node.js/Express    │    │  Python/FastAPI                 │ │
│  └─────────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start (Codespaces)

### 1. Install dependencies

```bash
cd teams_integration
npm install
```

### 2. Configure environment

Create `env/.env.local`:

```env
BOT_ID=<your-bot-id>
BOT_PASSWORD=<your-bot-password>
TEAMS_APP_ID=<your-teams-app-id>
```

### 3. Start the bot

```bash
npm run dev
```

### 4. Make port 3978 public

In Codespaces PORTS tab, right-click port 3978 → **Port Visibility** → **Public**

### 5. Register the bot

Update `BOT_ENDPOINT` in your Teams Toolkit provision with the Codespaces URL.

## Project Structure

```
teams_integration/
├── src/
│   ├── index.ts              # Express server & Bot Framework setup
│   ├── searchApp.ts          # Message extension logic
│   ├── config.ts             # Configuration management
│   └── adaptiveCards/
│       └── weatherCard.json  # Adaptive Card template
├── appPackage/
│   ├── manifest.json         # Teams app manifest
│   ├── color.png             # App icon (192x192)
│   └── outline.png           # App icon outline (32x32)
├── env/                      # Environment files (gitignored)
├── package.json
├── tsconfig.json
└── teamsapp.local.yml        # Teams Toolkit configuration
```

## API Integration

The bot calls the OutdoorMate API running on the same Codespace:

| Environment | API URL |
|-------------|---------|
| Codespaces | `http://localhost:8000` |
| External | Set `OUTDOORMATE_API_URL` env var |

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/messages` | POST | Bot Framework messages |
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_ID` | Yes | Microsoft Entra App ID |
| `BOT_PASSWORD` | Yes | Microsoft Entra App Secret |
| `BOT_TYPE` | No | Bot type (default: MultiTenant) |
| `OUTDOORMATE_API_URL` | No | API URL (default: http://localhost:8000) |
| `PORT` | No | Server port (default: 3978) |

## Development

### Running locally with Teams Toolkit

```bash
npm run dev:teamsfx
```

### Running with Test Tool (no Teams required)

```bash
npm run dev:teamsfx:testtool
```

### Building for production

```bash
npm run build
npm start
```

## Copilot Plugin

This Message Extension is designed to work as a Microsoft 365 Copilot plugin. The `semanticDescription` in the manifest helps Copilot understand when to invoke the extension.

Example Copilot prompts:
- "What's the weather in Sofia?"
- "Is the air quality good for jogging in Bansko?"
- "Check snow conditions in Pamporovo"

## Error Handling

The bot implements comprehensive error handling:
- Input sanitization to prevent injection attacks
- Timeout handling for API calls
- User-friendly error messages
- Structured logging for debugging

## License

MIT
