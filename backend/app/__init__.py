import os
from flask import Flask
from app.config import config_by_name, ProductionConfig
from app.extensions import db, migrate, cors, limiter
from app.errors import register_error_handlers
from app.logging_config import setup_logging
import app.models  # noqa: F401 - Register all database models with SQLAlchemy metadata


def create_app(config_name=None) -> Flask:
    """Flask application factory."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app_config = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(app_config)

    # Validate production secrets if running in production mode
    if config_name == "production":
        ProductionConfig.validate_production_secrets()

    # Dynamic environment binding for DATABASE_URL & SQLALCHEMY_DATABASE_URI
    if config_name != "testing":
        live_db_url = os.environ.get("DATABASE_URL")
        if live_db_url and live_db_url.strip():
            app.config["DATABASE_URL"] = live_db_url
            from app.config import normalize_database_url
            app.config["SQLALCHEMY_DATABASE_URI"] = normalize_database_url(live_db_url)


    # Initialize Logging
    setup_logging(app)
    app.logger.info(f"Starting Likshora Backend in '{config_name}' environment.")
    app.logger.info(f"Supabase Auth Configured: URL={bool(app.config.get('SUPABASE_URL'))}, Key={bool(app.config.get('SUPABASE_ANON_KEY'))}")

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS")}}, supports_credentials=True)
    limiter.init_app(app)

    # Register Blueprints
    from app.api import api_v1
    app.register_blueprint(api_v1)

    # Register Centralized Error Handlers
    register_error_handlers(app)

    # Global HTTP Security Response Headers Handler
    @app.after_request
    def apply_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if app.config.get("FLASK_ENV") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Start keep-alive pinger in production (prevents Render free tier sleep)
    from app.keep_alive import start_keep_alive
    start_keep_alive(app)

    return app
