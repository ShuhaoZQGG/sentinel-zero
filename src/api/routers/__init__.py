"""API routers for different endpoints."""

from . import processes
from . import schedules
from . import system
from . import config
from . import restart_policies

__all__ = ["processes", "schedules", "system", "config", "restart_policies"]