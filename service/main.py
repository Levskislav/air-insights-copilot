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

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Import routes and rate limiter from our routes module
from service.routes import router, limiter

# Import configuration and logging
from agent.config import config, VERSION
from agent.logging_config import logger, log_info

# Import HTTP client lifecycle handlers
from agent.http_client import startup as http_startup, shutdown as http_shutdown


# =============================================================================
# LIFESPAN CONTEXT MANAGER (replaces deprecated @app.on_event)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events in a modern, context-manager style.
    This replaces the deprecated @app.on_event("startup") decorator.
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Air & Insights Copilot v{VERSION}")
    logger.info(f"Swagger UI: http://localhost:{config.port}/docs")
    logger.info(f"Log level: {config.log_level}")
    logger.info(f"CORS origins: {config.cors_origins}")
    logger.info("=" * 60)
    
    # Validate required secrets
    missing = config.validate_required_secrets()
    if missing:
        logger.warning(f"Missing secrets: {', '.join(missing)}")
        logger.warning("Some features may not work correctly!")
    else:
        logger.info("All required secrets configured")
    
    # Initialize shared HTTP client
    await http_startup()
    
    yield  # Application runs here
    
    # Shutdown
    await http_shutdown()
    logger.info("Shutting down Air & Insights Copilot...")


# =============================================================================
# CREATE THE FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
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
    version=VERSION,
    lifespan=lifespan,
    contact={"name": "Air Insights Team"},
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# CORS (Cross-Origin Resource Sharing) middleware
# Origins loaded from CORS_ORIGINS env var (comma-separated) or "*" for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware - logs all requests with duration
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """Log request timing for all endpoints."""
    start = time.perf_counter()
    
    response = await call_next(request)
    
    duration_ms = (time.perf_counter() - start) * 1000
    
    # Log request (skip health check to reduce noise)
    if request.url.path != "/":
        log_info(
            f"{request.method} {request.url.path}",
            status=response.status_code,
            duration_ms=round(duration_ms, 1)
        )
    
    # Add timing header
    response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
    
    return response


# =============================================================================
# REGISTER ROUTES
# =============================================================================

# Include all routes from the router module
# This adds /analyze and /apod/today endpoints
app.include_router(router)


# =============================================================================
# HEALTH CHECK ENDPOINT
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
        "version": VERSION
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Detailed health check with dependency status.
    
    Checks:
    - API is running
    - Required secrets are configured
    - Cache status
    
    Returns 200 if healthy, includes warnings if any.
    """
    from agent.cache import cache_stats
    
    missing_secrets = config.validate_required_secrets()
    cache_info = cache_stats()
    
    checks = {
        "api": "ok",
        "secrets_configured": len(missing_secrets) == 0,
        "cache": "ok",
    }
    
    # Determine overall status
    all_ok = all(v == "ok" or v is True for v in checks.values())
    status = "healthy" if all_ok and not missing_secrets else "degraded"
    
    return {
        "status": status,
        "version": VERSION,
        "checks": checks,
        "cache": {
            "size": cache_info["size"],
            "maxsize": cache_info["maxsize"],
            "ttl_seconds": cache_info["ttl"],
        },
        "warnings": [f"Missing secret: {s}" for s in missing_secrets] if missing_secrets else []
    }
