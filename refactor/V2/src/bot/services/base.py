"""Clase base para servicios."""

from typing import TypeVar, Generic, Optional, List, Any, Dict, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
import structlog

from ..database.base import Base

T = TypeVar('T', bound=Base)
logger = structlog.get_logger()

class BaseService(Generic[T]):
    """Clase base para servicios que proporcionan operaciones comunes de CRUD."""
    
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
        self.logger = structlog.get_logger(service=self.__class__.__name__)
    
    async def get_by_id(self, session: AsyncSession, id: Any) -> Optional[T]:
        """Obtiene una entidad por su ID."""
        self.logger.debug("Obteniendo entidad por ID", id=id)
        return await session.get(self.model_class, id)
    
    async def get_all(self, session: AsyncSession) -> List[T]:
        """Obtiene todas las entidades."""
        self.logger.debug("Obteniendo todas las entidades")
        result = await session.execute(select(self.model_class))
        return list(result.scalars().all())
    
    async def create(self, session: AsyncSession, data: Dict[str, Any]) -> T:
        """Crea una nueva entidad."""
        self.logger.debug("Creando nueva entidad", data=data)
        entity = self.model_class(**data)
        session.add(entity)
        await session.flush()
        return entity
    
    async def update(self, session: AsyncSession, id: Any, data: Dict[str, Any]) -> Optional[T]:
        """Actualiza una entidad existente."""
        self.logger.debug("Actualizando entidad", id=id, data=data)
        entity = await self.get_by_id(session, id)
        if entity:
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            await session.flush()
        return entity
    
    async def update_bulk(self, session: AsyncSession, filter_dict: Dict[str, Any], data: Dict[str, Any]) -> int:
        """Actualiza múltiples entidades que cumplen con un filtro."""
        self.logger.debug("Actualizando múltiples entidades", filter=filter_dict, data=data)
        conditions = []
        for field, value in filter_dict.items():
            conditions.append(getattr(self.model_class, field) == value)
        
        query = update(self.model_class).where(*conditions).values(**data)
        result = await session.execute(query)
        return result.rowcount
    
    async def delete(self, session: AsyncSession, id: Any) -> bool:
        """Elimina una entidad por su ID."""
        self.logger.debug("Eliminando entidad", id=id)
        entity = await self.get_by_id(session, id)
        if entity:
            await session.delete(entity)
            await session.flush()
            return True
        return False
    
    async def delete_bulk(self, session: AsyncSession, filter_dict: Dict[str, Any]) -> int:
        """Elimina múltiples entidades que cumplen con un filtro."""
        self.logger.debug("Eliminando múltiples entidades", filter=filter_dict)
        conditions = []
        for field, value in filter_dict.items():
            conditions.append(getattr(self.model_class, field) == value)
        
        query = delete(self.model_class).where(*conditions)
        result = await session.execute(query)
        return result.rowcount