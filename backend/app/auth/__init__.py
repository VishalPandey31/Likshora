"""
Likshora Authentication Package (Supabase Auth).
"""

from app.auth.supabase_client import supabase_auth
from app.auth.decorators import require_auth, require_admin

__all__ = ["supabase_auth", "require_auth", "require_admin"]
