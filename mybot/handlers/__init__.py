"""Expose storyboard related routers for easy import."""

from .storyboard_admin import router as storyboard_admin_router
from .storyboard_player import router as storyboard_player_router

__all__ = [
    "storyboard_admin_router",
    "storyboard_player_router",
]

