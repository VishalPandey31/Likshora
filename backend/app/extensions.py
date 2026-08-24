import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()

# Use Redis for rate limiting storage in production (persistent across restarts)
# Falls back to in-memory storage for local development
_limiter_storage = os.environ.get("REDIS_URL", "memory://")
limiter = Limiter(key_func=get_remote_address, storage_uri=_limiter_storage, default_limits=[])

