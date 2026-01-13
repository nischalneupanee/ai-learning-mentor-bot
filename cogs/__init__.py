"""
Cogs package initialization.
"""

from cogs.tracking import TrackingCog
from cogs.dashboard import DashboardCog
from cogs.admin import AdminCog

__all__ = [
    "TrackingCog",
    "DashboardCog",
    "AdminCog",
]
