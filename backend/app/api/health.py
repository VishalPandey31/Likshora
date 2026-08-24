import os
import time

from flask import jsonify, current_app
from sqlalchemy import text
from app.api import api_v1
from app.extensions import db


@api_v1.route("/health", methods=["GET"])
def health_check():
    """General API health check endpoint."""
    return jsonify({
        "success": True,
        "message": "Likshora backend is running",
        "service": "Likshora API",
        "version": "v1"
    }), 200


@api_v1.route("/health/db", methods=["GET"])
def db_health_check():
    """Database connectivity health check endpoint."""
    raw_db_url = os.environ.get("DATABASE_URL") if "DATABASE_URL" in os.environ else current_app.config.get("DATABASE_URL")

    if not raw_db_url or not raw_db_url.strip():
        return jsonify({
            "success": False,
            "backend": "healthy",
            "database": "disconnected",
            "error": "DATABASE_URL environment variable is missing or unconfigured"
        }), 503

    start_time = time.time()
    try:
        # Perform lightweight check query
        db.session.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return jsonify({
            "success": True,
            "backend": "healthy",
            "database": "connected",
            "latency_ms": latency_ms
        }), 200
    except Exception as exc:
        # Log exact error on server side safely
        current_app.logger.error(f"Database health check failed: {type(exc).__name__}")
        # Return generic safe message to client without exposing credentials or internal stack traces
        return jsonify({
            "success": False,
            "backend": "healthy",
            "database": "disconnected",
            "error": "Unable to connect to Supabase PostgreSQL database"
        }), 503
