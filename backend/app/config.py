from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Database
    DATABASE_URL: str = "postgresql://invoiceflow:invoiceflow@localhost:5432/invoiceflow"

    # Data paths
    DATA_PATH: Path = Path("/app/data")
    INCOMING_PATH: Path = DATA_PATH / "incoming"
    PROCESSING_PATH: Path = DATA_PATH / "processing"
    APPROVED_PATH: Path = DATA_PATH / "approved"
    EXPORT_ACCOUNTING_PATH: Path = DATA_PATH / "export" / "accounting"
    EXPORT_DMS_PATH: Path = DATA_PATH / "export" / "dms"

    # Paperless-ngx
    PAPERLESS_URL: str = "http://paperless:8000"
    PAPERLESS_TOKEN: Optional[str] = None

    # JWT Authentication
    JWT_SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # Watcher Service API Key (for file-watcher → backend auth)
    WATCHER_API_KEY: str = "change-me-watcher-key"

    # Default admin credentials (used on first startup)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me-admin-password"

    # API
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "InvoiceFlow"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    # Zusätzliche Origins kommasepariert, z.B.: http://192.168.1.10:3000
    CORS_EXTRA_ORIGINS: str = ""

    # File Upload
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB in bytes
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".xml"]
    ALLOWED_MIME_TYPES: list[str] = [
        "application/pdf",
        "text/xml",
        "application/xml",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
