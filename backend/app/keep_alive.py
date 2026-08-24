"""
Keep-Alive Self-Ping — Prevents Render Free Tier Cold Starts.

Spawns a lightweight background thread that pings the app's own
health endpoint every 10 minutes, keeping the Gunicorn workers warm.

Only activates when FLASK_ENV=production to avoid interfering with
local development or automated tests.
"""
import threading
import time
import os
import requests


def start_keep_alive(app):
    """Start background keep-alive pinger in production environments only."""
    if app.config.get("TESTING") or os.environ.get("FLASK_ENV") != "production":
        return

    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not render_url:
        app.logger.info("RENDER_EXTERNAL_URL not set — keep-alive disabled.")
        return

    health_url = f"{render_url.rstrip('/')}/api/v1/health"
    interval = int(os.environ.get("KEEP_ALIVE_INTERVAL", 600))  # 10 minutes

    def ping_loop():
        while True:
            time.sleep(interval)
            try:
                resp = requests.get(health_url, timeout=10)
                app.logger.debug(f"Keep-alive ping: {resp.status_code}")
            except Exception as e:
                app.logger.warning(f"Keep-alive ping failed: {e}")

    thread = threading.Thread(target=ping_loop, daemon=True, name="keep-alive")
    thread.start()
    app.logger.info(f"Keep-alive started: pinging {health_url} every {interval}s")
