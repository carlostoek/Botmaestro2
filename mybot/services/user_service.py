# mybot/services/user_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User # Asegúrate de que tu modelo User esté accesible aquí
import logging

logger = logging.getLogger(__name__)

class UserService:
    """
    Servicio para manejar operaciones relacionadas con usuarios,
    como la verificación de membresía VIP.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: int) -> User:
        """Obtiene un usuario por su ID."""
        return await self.session.get(User, user_id)

    async def is_vip_member(self, user_id: int) -> bool:
        """
        Verifica si un usuario es miembro VIP.
        Esta es una implementación de ejemplo.
        Debes ajustarla según cómo defines el estado VIP de un usuario
        en tu base de datos (ej. un campo 'is_vip', una relación de suscripción, etc.).
        """
        try:
            user = await self.get_user(user_id)
            if user and user.is_vip: # Asumiendo que tienes un campo 'is_vip' en tu modelo User
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking VIP status for user {user_id}: {e}")
            return False

    # Puedes añadir más métodos relacionados con el usuario aquí, por ejemplo:
    # async def update_user_profile(self, user_id: int, new_data: dict):
    #     # ... lógica para actualizar el perfil del usuario ...
    #     pass

