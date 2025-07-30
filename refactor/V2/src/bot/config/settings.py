"""Configuración de la aplicación basada en variables de entorno."""

from typing import List, Optional, Set
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""
    
    # Bot settings
    BOT_TOKEN: str
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"
    USE_WEBHOOK: bool = False
    
    # Database settings
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False
    
    # Admin settings
    ADMIN_USER_IDS: str = ""
    
    @field_validator("ADMIN_USER_IDS", mode="before")
    def parse_admin_ids(cls, v: str) -> str:
        return v
    
    @property
    def admin_ids(self) -> Set[int]:
        """Devuelve la lista de IDs de administradores."""
        if not self.ADMIN_USER_IDS:
            return set()
        return {int(x.strip()) for x in self.ADMIN_USER_IDS.split(",") if x.strip()}
    
    # Channel settings
    VIP_CHANNEL_ID: Optional[int] = None
    FREE_CHANNEL_ID: Optional[int] = None
    
    # Feature flags
    ENABLE_ANALYTICS: bool = False
    ENABLE_BACKGROUND_TASKS: bool = True
    ENABLE_EMOTIONAL_SYSTEM: bool = True
    
    # Task scheduler
    TASK_SCHEDULER_TIMEZONE: str = "UTC"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    # Security
    API_ID: Optional[str] = None
    API_HASH: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Singleton instance
settings = Settings()