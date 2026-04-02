import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import invoices
from app.api import auth as auth_router
from app.api import admin as admin_router
from app.database import engine, Base
from app.models import invoice  # noqa: F401 – ensures models are registered
from app.models import user as user_model  # noqa: F401
from app.models import setting as setting_model  # noqa: F401
import requests as http_requests

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("app").setLevel(logging.INFO)

# Create all tables on startup (includes new users + settings tables)
Base.metadata.create_all(bind=engine)

# Migrate: add new columns if they don't exist yet (PostgreSQL supports IF NOT EXISTS)
from sqlalchemy import text as _text

with engine.connect() as _conn:
    _conn.execute(_text(
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS processing_error TEXT"
    ))
    _conn.execute(_text(
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS processing_attempts INTEGER DEFAULT 0"
    ))
    _conn.execute(_text(
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS supplier_email VARCHAR(255)"
    ))
    _conn.execute(_text(
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS supplier_electronic_address VARCHAR(255)"
    ))
    _conn.execute(_text(
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255)"
    ))
    _conn.commit()

# Initialize admin user and default settings
from app.database import SessionLocal as _SessionLocal
from app.models.user import User as _User
from app.models.setting import Setting as _Setting
from app.core.security import hash_password as _hash_password

with _SessionLocal() as _db:
    # Create default admin user if not exists
    if not _db.query(_User).filter(_User.username == settings.ADMIN_USERNAME).first():
        _db.add(_User(
            username=settings.ADMIN_USERNAME,
            hashed_password=_hash_password(settings.ADMIN_PASSWORD),
            is_superuser=True,
            is_active=True,
        ))
        _db.flush()
        logging.getLogger("app").info("Default admin user created")

    # Insert default settings (ON CONFLICT DO NOTHING via Python check)
    _defaults = [
        ("PAPERLESS_URL", settings.PAPERLESS_URL or "", "URL der Paperless-ngx Instanz"),
        ("PAPERLESS_TOKEN", settings.PAPERLESS_TOKEN or "", "API-Token für Paperless-ngx"),
        ("PAPERLESS_CORRESPONDENT_GROUP_VIEW", "", "Gruppen-ID für Anzeigen-Recht auf neue Korrespondenten"),
        ("PAPERLESS_CORRESPONDENT_GROUP_CHANGE", "", "Gruppen-ID für Bearbeiten-Recht auf neue Korrespondenten"),
    ]
    for _key, _val, _desc in _defaults:
        if not _db.query(_Setting).filter(_Setting.key == _key).first():
            _db.add(_Setting(key=_key, value=_val, description=_desc))

    _db.commit()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="InvoiceFlow - Automated Invoice Processing System",
    version="1.0.0",
)

# Configure CORS
_cors_origins = settings.CORS_ORIGINS + [
    o.strip() for o in settings.CORS_EXTRA_ORIGINS.split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(invoices.router, prefix=settings.API_V1_PREFIX)
app.include_router(invoices.watcher_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router.router)
app.include_router(admin_router.router)


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
    """Check connectivity to Paperless-ngx (reads URL/token from DB settings)"""
    from app.database import SessionLocal
    from app.models.setting import Setting

    with SessionLocal() as db:
        def _get(key, fallback):
            row = db.query(Setting).filter(Setting.key == key).first()
            return (row.value or fallback) if row else fallback

        url = (_get("PAPERLESS_URL", settings.PAPERLESS_URL) or "").rstrip("/")
        token = _get("PAPERLESS_TOKEN", settings.PAPERLESS_TOKEN or "")

    token_configured = bool(token)
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Token {token}"

        response = http_requests.get(f"{url}/api/", headers=headers, timeout=5)
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
