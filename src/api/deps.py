"""Dependency injection and global instances for API."""

from typing import Optional
import structlog

from src.core.process_manager import ProcessManager
from src.core.scheduler import ProcessScheduler as Scheduler
from src.config.config_manager import ConfigManager

logger = structlog.get_logger()

# Global instances - will be initialized on startup
process_manager: Optional[ProcessManager] = None
scheduler: Optional[Scheduler] = None
config_manager: Optional[ConfigManager] = None


def get_process_manager() -> ProcessManager:
    """Get process manager instance."""
    if process_manager is None:
        raise RuntimeError("Process manager not initialized")
    return process_manager


def get_scheduler() -> Scheduler:
    """Get scheduler instance."""
    if scheduler is None:
        raise RuntimeError("Scheduler not initialized")
    return scheduler


def get_config_manager() -> ConfigManager:
    """Get config manager instance."""
    if config_manager is None:
        raise RuntimeError("Config manager not initialized")
    return config_manager


def initialize_managers():
    """Initialize all manager instances."""
    global process_manager, scheduler, config_manager
    
    logger.info("Initializing managers")
    
    process_manager = ProcessManager()
    scheduler = Scheduler()
    config_manager = ConfigManager("config.yaml")
    
    logger.info("Managers initialized")