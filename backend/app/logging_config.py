import logging
import sys


def setup_logging(app):
    """Configure structured, secure application logging."""
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO

    # Custom formatter for clean output
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)

    # Attach to Flask app logger
    app.logger.handlers.clear()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(log_level)

    app.logger.info("Likshora backend logger initialized cleanly.")
