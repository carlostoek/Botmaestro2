"""Programador de tareas."""

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import pytz

from ..config import settings
from ..tasks.daily import schedule_daily_tasks
from ..tasks.maintenance import schedule_maintenance_tasks

logger = structlog.get_logger()

def setup_scheduler() -> AsyncIOScheduler:
    """Configura el programador de tareas."""
    
    # Configurar timezone
    timezone = pytz.timezone(settings.TASK_SCHEDULER_TIMEZONE)
    
    # Configurar jobstores y executors
    jobstores = {
        'default': MemoryJobStore()
    }
    
    executors = {
        'default': ThreadPoolExecutor(20)
    }
    
    # Crear scheduler
    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        timezone=timezone
    )
    
    # Registrar tareas
    schedule_daily_tasks(scheduler)
    schedule_maintenance_tasks(scheduler)
    
    logger.info("Programador de tareas configurado")
    
    return scheduler