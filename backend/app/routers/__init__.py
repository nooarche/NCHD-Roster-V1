# backend/app/routers/__init__.py

from .api import router as posts_router      # /posts
from .groups import router as groups_router  # /groups

__all__ = ["posts_router", "groups_router"]
