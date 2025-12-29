#!/bin/bash
# Start OutdoorMate services

# Install Teams bot dependencies if needed
if [ ! -d "teams_integration/node_modules" ]; then
    cd teams_integration && npm install && cd ..
fi

# Start FastAPI (port 8000)
uvicorn service.main:app --host 0.0.0.0 --port 8000 &

# Start Teams Bot (port 3978)
cd teams_integration && npm run dev:teamsfx
