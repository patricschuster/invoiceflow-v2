import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import invoices
from app.database import engine, Base
from app.models import invoice  # noqa: F401 – ensures models are registered
import requests as http_requests

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("app").setLevel(logging.INFO)

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="InvoiceFlow - Automated Invoice Processing System",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(invoices.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to InvoiceFlow API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }


@app.get("/api/health/paperless")
async def paperless_health():
    """Check connectivity to Paperless-ngx"""
    url = settings.PAPERLESS_URL.rstrip("/")
    token = settings.PAPERLESS_TOKEN
    token_configured = bool(token)

    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Token {token}"

        response = http_requests.get(
            f"{url}/api/",
            headers=headers,
            timeout=5,
        )
        connected = response.status_code in (200, 301, 302)
        return {
            "connected": connected,
            "url": url,
            "token_configured": token_configured,
            "status_code": response.status_code,
        }
    except http_requests.exceptions.ConnectionError:
        return {"connected": False, "url": url, "token_configured": token_configured, "error": "Verbindung abgelehnt"}
    except http_requests.exceptions.Timeout:
        return {"connected": False, "url": url, "token_configured": token_configured, "error": "Timeout"}
    except Exception as e:
        return {"connected": False, "url": url, "token_configured": token_configured, "error": str(e)}
