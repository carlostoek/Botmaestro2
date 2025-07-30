"""Punto de entrada principal para el bot."""

import asyncio
import logging
import structlog

from .core.bootstrap import bootstrap
from .config import settings

# Configuración de logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=settings.LOG_FILE,
)

# Configuración de structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def main():
    """Función principal que inicia el bot."""
    logger.info("Iniciando Diana Bot v2.0")
    
    try:
        await bootstrap()
    except Exception as e:
        logger.exception("Error al iniciar el bot", error=str(e))
        raise
    
    logger.info("Bot detenido")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.exception("Error fatal", error=str(e))