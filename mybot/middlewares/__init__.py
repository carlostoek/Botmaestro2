# No coloques mybot como módulo, es la raíz del proyecto
from .points_middleware import PointsMiddleware
from .user_middleware import UserRegistrationMiddleware

__all__ = [
    "PointsMiddleware",
    "UserRegistrationMiddleware",
]
