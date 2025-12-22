"""
service/main.py
===============
FastAPI application entry point.

This is the main file that creates and configures the FastAPI app.
Run with: uvicorn service.main:app --reload --port 8000

Key concepts:
- FastAPI() creates the web application
- app.include_router() adds routes from other files
- Swagger UI is auto-generated at /docs
"""

# Load environment variables from .env file BEFORE importing other modules
# This must be at the very top to ensure all modules see the env vars
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes from our routes module
from service.routes import router

# =============================================================================
# CREATE THE FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    # App metadata (shows in Swagger UI)
    title="Air & Insights Copilot",
    description="""
    Agentic assistant that provides air quality and weather guidance.
    
    ## Features
    - **Air Quality**: PM2.5 and PM10 data from Open-Meteo
    - **Weather**: Temperature forecast from Open-Meteo  
    - **AI Guidance**: LLM-generated recommendations via GitHub Models
    - **NASA APOD**: Astronomy Picture of the Day (optional)
    
    ## Attribution
    Weather data by Open-Meteo.com
    """,
    version="0.1.0",
    
    # Contact info (optional, shows in Swagger)
    contact={
        "name": "Air Insights Team",
    },
)

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# CORS (Cross-Origin Resource Sharing) middleware
# This allows our web UI (running on a different port) to call the API
app.add_middleware(
    CORSMiddleware,
    # In production, replace "*" with specific origins like ["https://yourdomain.com"]
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# =============================================================================
# REGISTER ROUTES
# =============================================================================

# Include all routes from the router module
# This adds /analyze and /apod/today endpoints
app.include_router(router)


# =============================================================================
# ROOT ENDPOINT (optional, for health check)
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint - simple health check.
    
    Returns a welcome message to confirm the API is running.
    Useful for load balancers and monitoring systems.
    """
    return {
        "message": "Welcome to Air & Insights Copilot API",
        "docs": "/docs",
        "version": "0.1.0"
    }