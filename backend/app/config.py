import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
base_dir = Path(__file__).resolve().parent.parent
load_dotenv(base_dir / ".env")


def normalize_database_url(url: str | None) -> str:
    """Normalize legacy postgres:// URI scheme to postgresql:// for SQLAlchemy compatibility.
    Provides a fallback PostgreSQL URI if none is specified so Flask-SQLAlchemy initializes cleanly.
    """
    if not url or not url.strip():
        return "postgresql://unconfigured_user:unconfigured_pass@localhost:5432/unconfigured_db"
    url = url.strip()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def parse_cors_origins(origins_str: str | None) -> list[str]:
    """Parse comma-separated CORS origins string into a clean list."""
    default_origins = [
        "http://localhost:5500", "http://127.0.0.1:5500",
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:8000", "http://127.0.0.1:8000",
        "http://localhost:5000", "http://127.0.0.1:5000",
        "null", "*"
    ]
    if not origins_str:
        return default_origins
    origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    for d in default_origins:
        if d not in origins:
            origins.append(d)
    return origins


class Config:
    """Base application configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "likshora-dev-secret-key-change-in-production")
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = False
    TESTING = False

    # Database Configuration
    DATABASE_URL = os.environ.get("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI = normalize_database_url(DATABASE_URL)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Supabase Platform Credentials
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    # CORS Configuration
    CORS_ORIGINS = parse_cors_origins(os.environ.get("CORS_ORIGINS"))

    # Razorpay Payment Gateway Credentials
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
    RAZORPAY_CURRENCY = os.environ.get("RAZORPAY_CURRENCY", "INR")

    # Shiprocket Shipping Integration Credentials
    SHIPROCKET_EMAIL = os.environ.get("SHIPROCKET_EMAIL", "")
    SHIPROCKET_PASSWORD = os.environ.get("SHIPROCKET_PASSWORD", "")
    SHIPROCKET_BASE_URL = os.environ.get("SHIPROCKET_BASE_URL", "https://apiv2.shiprocket.in/v1/external").rstrip("/")
    SHIPROCKET_WEBHOOK_TOKEN = os.environ.get("SHIPROCKET_WEBHOOK_TOKEN", "")
    SHIPROCKET_PICKUP_LOCATION = os.environ.get("SHIPROCKET_PICKUP_LOCATION", "Primary")
    SHIPROCKET_DEFAULT_LENGTH = float(os.environ.get("SHIPROCKET_DEFAULT_LENGTH", 10))
    SHIPROCKET_DEFAULT_BREADTH = float(os.environ.get("SHIPROCKET_DEFAULT_BREADTH", 10))
    SHIPROCKET_DEFAULT_HEIGHT = float(os.environ.get("SHIPROCKET_DEFAULT_HEIGHT", 10))
    SHIPROCKET_DEFAULT_WEIGHT = float(os.environ.get("SHIPROCKET_DEFAULT_WEIGHT", 0.5))


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = True
    TEST_DB_URL = os.environ.get("TEST_DATABASE_URL")
    if TEST_DB_URL and TEST_DB_URL.strip():
        SQLALCHEMY_DATABASE_URI = normalize_database_url(TEST_DB_URL)
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"



class ProductionConfig(Config):
    """Production environment configuration with strict secret validation."""

    DEBUG = False
    TESTING = False

    @classmethod
    def validate_production_secrets(cls):
        """Verify that insecure development fallback keys are not active in production."""
        secret_key = os.environ.get("SECRET_KEY")
        if not secret_key or secret_key.strip() in [
            "likshora-dev-secret-key-change-in-production",
            "secret",
            "123456",
            "change-me",
        ]:
            raise RuntimeError("CRITICAL SECURITY RISK: Insecure or default SECRET_KEY configured in Production mode!")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
