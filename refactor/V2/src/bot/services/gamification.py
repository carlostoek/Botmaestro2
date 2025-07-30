"""Servicio para el sistema de gamificación."""

from typing import Optional, Dict, Any, List, Tuple
import structlog
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_, or_, desc, func, text

from .base import BaseService
from ..database.models.gamification import (
    UserPoints,
    Achievement,
    UserAchievement,
    Mission,
    UserMission,
    MissionTypeEnum,
    MissionStatusEnum
)
from ..config.constants import USER_LEVELS

logger = structlog.get_logger()

class GamificationService:
    """Servicio para gestionar el sistema de gamificación."""
    
    def __init__(self):
        self.logger = structlog.get_logger(service="GamificationService")
        self.points_service = PointsService()
        self.achievement_service = AchievementService()
        self.mission_service = MissionService()
    
    async def get_user_profile(
        self, session: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """Obtiene el perfil de gamificación completo de un usuario."""
        self.logger.debug("Obteniendo perfil de gamificación", user_id=user_id)
        
        # Obtener puntos
        points = await self.points_service.get_or_create_points(session, user_id)
        
        # Obtener nivel
        level_info = self.calculate_level(points.current_points)
        
        # Obtener logros
        achievements = await self.achievement_service.get_user_achievements(session, user_id)
        
        # Obtener misiones activas
        active_missions = await self.mission_service.get_active_missions(session, user_id)
        
        # Formatear respuesta
        result = {
            "points": {
                "current": points.current_points,
                "total_earned": points.total_earned,
                "total_spent": points.total_spent,
                "sources": {
                    "messages": points.points_from_messages,
                    "reactions": points.points_from_reactions,
                    "missions": points.points_from_missions,
                    "dailygift": points.points_from_dailygift,
                    "minigames": points.points_from_minigames,
                    "narrative": points.points_from_narrative
                },
                "multipliers": points.active_multipliers
            },
            "level": {
                "current": level_info["current_level"],
                "name": level_info["level_name"],
                "progress": level_info["progress_percent"],
                "points_to_next_level": level_info["points_to_next_level"]
            },
            "achievements": {
                "completed": sum(1 for a in achievements if a["is_completed"]),
                "total": len(achievements),
                "progress": sum(a["progress"] for a in achievements) / len(achievements) if achievements else 0,
                "recent": [
                    a for a in achievements 
                    if a["is_completed"] and a["completed_at"] 
                    and (datetime.now() - a["completed_at"]).days < 7
                ][:3]
            },
            "missions": {
                "active": len(active_missions),
                "completed_today": sum(
                    1 for m in active_missions 
                    if m["status"] == MissionStatusEnum.COMPLETED.value
                    and m["completed_at"] 
                    and (datetime.now() - m["completed_at"]).days < 1
                ),
                "expires_soon": [
                    m for m in active_missions
                    if m["status"] == MissionStatusEnum.IN_PROGRESS.value
                    and m["expires_at"]
                    and (m["expires_at"] - datetime.now()).total_seconds() < 86400  # 24 horas
                ][:3]
            }
        }
        
        return result
    
    async def award_points(
        self, session: AsyncSession, user_id: int, amount: float, source: str, 
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Otorga puntos a un usuario."""
        self.logger.debug("Otorgando puntos", user_id=user_id, amount=amount, source=source)
        
        # Validar monto
        if amount <= 0:
            self.logger.warning("Intento de otorgar puntos negativos o cero", amount=amount)
            raise ValueError("La cantidad de puntos debe ser positiva")
        
        # Obtener puntos actuales
        points = await self.points_service.get_or_create_points(session, user_id)
        
        # Actualizar puntos según la fuente
        update_data = {
            "current_points": points.current_points + amount,
            "total_earned": points.total_earned + amount
        }
        
        # Actualizar estadísticas específicas por fuente
        if source == "message":
            update_data["points_from_messages"] = points.points_from_messages + amount
        elif source == "reaction":
            update_data["points_from_reactions"] = points.points_from_reactions + amount
        elif source == "mission":
            update_data["points_from_missions"] = points.points_from_missions + amount
        elif source == "dailygift":
            update_data["points_from_dailygift"] = points.points_from_dailygift + amount
        elif source == "minigame":
            update_data["points_from_minigames"] = points.points_from_minigames + amount
        elif source == "narrative":
            update_data["points_from_narrative"] = points.points_from_narrative + amount
        
        # Actualizar puntos
        updated_points = await self.points_service.update(session, points.id, update_data)
        
        # Obtener nivel antes y después
        old_level = self.calculate_level(points.current_points)["current_level"]
        new_level = self.calculate_level(updated_points.current_points)["current_level"]
        
        # Verificar si subió de nivel
        level_up = new_level > old_level
        
        # Formatear respuesta
        result = {
            "user_id": user_id,
            "points_awarded": amount,
            "current_points": updated_points.current_points,
            "source": source,
            "description": description,
            "level_up": level_up,
            "old_level": old_level,
            "new_level": new_level if level_up else None,
            "new_level_name": USER_LEVELS[new_level]["name"] if level_up else None
        }
        
        # Verificar logros relacionados con puntos
        if level_up:
            await self.check_level_achievements(session, user_id, new_level)
        
        return result
    
    async def spend_points(
        self, session: AsyncSession, user_id: int, amount: float, reason: str
    ) -> Dict[str, Any]:
        """Gasta puntos de un usuario."""
        self.logger.debug("Gastando puntos", user_id=user_id, amount=amount, reason=reason)
        
        # Validar monto
        if amount <= 0:
            self.logger.warning("Intento de gastar puntos negativos o cero", amount=amount)
            raise ValueError("La cantidad de puntos debe ser positiva")
        
        # Obtener puntos actuales
        points = await self.points_service.get_or_create_points(session, user_id)
        
        # Verificar si tiene suficientes puntos
        if points.current_points < amount:
            self.logger.warning(
                "Puntos insuficientes", 
                current=points.current_points, 
                requested=amount
            )
            raise ValueError("Puntos insuficientes")
        
        # Actualizar puntos
        update_data = {
            "current_points": points.current_points - amount,
            "total_spent": points.total_spent + amount
        }
        
        updated_points = await self.points_service.update(session, points.id, update_data)
        
        # Formatear respuesta
        result = {
            "user_id": user_id,
            "points_spent": amount,
            "current_points": updated_points.current_points,
            "reason": reason,
            "success": True
        }
        
        return result
    
    async def get_leaderboard(
        self, session: AsyncSession, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene la tabla de clasificación de puntos."""
        self.logger.debug("Obteniendo tabla de clasificación", limit=limit)
        
        # Obtener los usuarios con más puntos
        leaderboard = await self.points_service.get_top_users(session, limit)
        
        return leaderboard
    
    async def complete_achievement(
        self, session: AsyncSession, user_id: int, achievement_key: str
    ) -> Dict[str, Any]:
        """Completa un logro para un usuario."""
        self.logger.debug("Completando logro", user_id=user_id, achievement=achievement_key)
        
        # Obtener el logro
        achievement = await self.achievement_service.get_by_key(session, achievement_key)
        if not achievement:
            self.logger.error("Logro no encontrado", achievement_key=achievement_key)
            raise ValueError(f"Logro {achievement_key} no encontrado")
        
        # Obtener el logro del usuario
        user_achievement = await self.achievement_service.get_user_achievement(
            session, user_id, achievement.id
        )
        
        if user_achievement and user_achievement.is_completed:
            self.logger.warning("Logro ya completado", achievement_key=achievement_key)
            return {
                "user_id": user_id,
                "achievement": {
                    "key": achievement.key,
                    "name": achievement.name,
                    "description": achievement.description
                },
                "already_completed": True,
                "completed_at": user_achievement.completed_at.isoformat() if user_achievement.completed_at else None,
                "points_awarded": 0
            }
        
        # Si no existe, crearlo
        if not user_achievement:
            user_achievement_data = {
                "user_id": user_id,
                "achievement_id": achievement.id,
                "is_completed": True,
                "progress": 1.0,
                "completed_at": datetime.now(),
                "completion_data": {}
            }
            
            user_achievement = await self.achievement_service.create_user_achievement(
                session, user_achievement_data
            )
        else:
            # Actualizar si existe pero no está completado
            await self.achievement_service.update_user_achievement(
                session, user_achievement.id, {
                    "is_completed": True,
                    "progress": 1.0,
                    "completed_at": datetime.now()
                }
            )
        
        # Otorgar recompensa de puntos si existe
        points_awarded = 0
        if achievement.points_reward > 0:
            result = await self.award_points(
                session, user_id, achievement.points_reward, "achievement",
                f"Logro completado: {achievement.name}"
            )
            points_awarded = result["points_awarded"]
        
        # Formatear respuesta
        result = {
            "user_id": user_id,
            "achievement": {
                "key": achievement.key,
                "name": achievement.name,
                "description": achievement.description
            },
            "completed": True,
            "completed_at": datetime.now().isoformat(),
            "points_awarded": points_awarded
        }
        
        return result
    
    async def update_achievement_progress(
        self, session: AsyncSession, user_id: int, achievement_key: str, progress: float
    ) -> Dict[str, Any]:
        """Actualiza el progreso de un logro para un usuario."""
        self.logger.debug(
            "Actualizando progreso de logro", 
            user_id=user_id, 
            achievement=achievement_key, 
            progress=progress
        )
        
        # Validar progreso
        if progress < 0 or progress > 1:
            self.logger.warning("Progreso inválido", progress=progress)
            raise ValueError("El progreso debe estar entre 0 y 1")
        
        # Obtener el logro
        achievement = await self.achievement_service.get_by_key(session, achievement_key)
        if not achievement:
            self.logger.error("Logro no encontrado", achievement_key=achievement_key)
            raise ValueError(f"Logro {achievement_key} no encontrado")
        
        # Obtener o crear el logro del usuario
        user_achievement = await self.achievement_service.get_user_achievement(
            session, user_id, achievement.id
        )
        
        completed = False
        completion_time = None
        
        if not user_achievement:
            # Si no existe, crearlo
            is_completed = progress >= 1.0
            user_achievement_data = {
                "user_id": user_id,
                "achievement_id": achievement.id,
                "is_completed": is_completed,
                "progress": progress,
                "completed_at": datetime.now() if is_completed else None,
                "completion_data": {}
            }
            
            user_achievement = await self.achievement_service.create_user_achievement(
                session, user_achievement_data
            )
            
            completed = is_completed
            completion_time = datetime.now() if is_completed else None
        else:
            # Si ya está completado, no actualizar
            if user_achievement.is_completed:
                self.logger.info("Logro ya completado, no se actualiza", achievement_key=achievement_key)
                return {
                    "user_id": user_id,
                    "achievement": {
                        "key": achievement.key,
                        "name": achievement.name
                    },
                    "already_completed": True,
                    "previous_progress": user_achievement.progress,
                    "current_progress": user_achievement.progress,
                    "completed_at": user_achievement.completed_at.isoformat() if user_achievement.completed_at else None
                }
            
            # Si el progreso es mayor o igual a 1, completar el logro
            is_completed = progress >= 1.0
            update_data = {
                "progress": progress
            }
            
            if is_completed:
                update_data["is_completed"] = True
                update_data["completed_at"] = datetime.now()
                completed = True
                completion_time = datetime.now()
            
            await self.achievement_service.update_user_achievement(
                session, user_achievement.id, update_data
            )
        
        # Otorgar recompensa si se completó
        points_awarded = 0
        if completed and achievement.points_reward > 0:
            result = await self.award_points(
                session, user_id, achievement.points_reward, "achievement",
                f"Logro completado: {achievement.name}"
            )
            points_awarded = result["points_awarded"]
        
        # Formatear respuesta
        result = {
            "user_id": user_id,
            "achievement": {
                "key": achievement.key,
                "name": achievement.name
            },
            "previous_progress": user_achievement.progress if user_achievement else 0,
            "current_progress": progress,
            "completed": completed,
            "completed_at": completion_time.isoformat() if completion_time else None,
            "points_awarded": points_awarded
        }
        
        return result
    
    async def start_mission(
        self, session: AsyncSession, user_id: int, mission_key: str
    ) -> Dict[str, Any]:
        """Inicia una misión para un usuario."""
        self.logger.debug("Iniciando misión", user_id=user_id, mission=mission_key)
        
        # Obtener la misión
        mission = await self.mission_service.get_by_key(session, mission_key)
        if not mission:
            self.logger.error("Misión no encontrada", mission_key=mission_key)
            raise ValueError(f"Misión {mission_key} no encontrada")
        
        # Verificar si la misión está activa
        if not mission.is_active:
            self.logger.warning("Misión inactiva", mission_key=mission_key)
            raise ValueError(f"Misión {mission_key} no está activa")
        
        # Verificar si ya tiene la misión
        user_mission = await self.mission_service.get_user_mission(
            session, user_id, mission.id
        )
        
        if user_mission:
            if user_mission.status == MissionStatusEnum.COMPLETED:
                self.logger.warning("Misión ya completada", mission_key=mission_key)
                return {
                    "user_id": user_id,
                    "mission": {
                        "key": mission.key,
                        "title": mission.title
                    },
                    "already_completed": True,
                    "status": user_mission.status.value,
                    "completed_at": user_mission.completed_at.isoformat() if user_mission.completed_at else None
                }
            elif user_mission.status == MissionStatusEnum.IN_PROGRESS:
                self.logger.warning("Misión ya en progreso", mission_key=mission_key)
                return {
                    "user_id": user_id,
                    "mission": {
                        "key": mission.key,
                        "title": mission.title
                    },
                    "already_in_progress": True,
                    "status": user_mission.status.value,
                    "started_at": user_mission.started_at.isoformat() if user_mission.started_at else None,
                    "expires_at": user_mission.expires_at.isoformat() if user_mission.expires_at else None
                }
        
        # Calcular fecha de expiración
        expires_at = None
        if mission.time_limit_hours:
            expires_at = datetime.now() + timedelta(hours=mission.time_limit_hours)
        
        # Crear misión de usuario
        user_mission_data = {
            "user_id": user_id,
            "mission_id": mission.id,
            "status": MissionStatusEnum.IN_PROGRESS,
            "progress": {},
            "progress_percentage": 0.0,
            "started_at": datetime.now(),
            "expires_at": expires_at
        }
        
        user_mission = await self.mission_service.create_user_mission(
            session, user_mission_data
        )
        
        # Formatear respuesta
        result = {
            "user_id": user_id,
            "mission": {
                "key": mission.key,
                "title": mission.title,
                "description": mission.description,
                "mission_type": mission.mission_type.value,
                "points_reward": mission.points_reward
            },
            "status": user_mission.status.value,
            "started_at": user_mission.started_at.isoformat() if user_mission.started_at else None,
            "expires_at": user_mission.expires_at.isoformat() if user_mission.expires_at else None
        }
        
        return result
    
    async def update_mission_progress(
        self, session: AsyncSession, user_id: int, mission_key: str, 
        progress: Dict[str, Any], progress_percentage: Optional[float] = None
    ) -> Dict[str, Any]:
        """Actualiza el progreso de una misión para un usuario."""
        self.logger.debug(
            "Actualizando progreso de misión", 
            user_id=user_id, 
            mission=mission_key, 
            progress=progress
        )
        
        # Obtener la misión
        mission = await self.mission_service.get_by_key(session, mission_key)
        if not mission:
            self.logger.error("Misión no encontrada", mission_key=mission_key)
            raise ValueError(f"Misión {mission_key} no encontrada")
        
        # Obtener la misión del usuario
        user_mission = await self.mission_service.get_user_mission(
            session, user_id, mission.id
        )
        
        if not user_mission:
            self.logger.warning("Misión no iniciada", mission_key=mission_key)
            raise ValueError(f"Misión {mission_key} no ha sido iniciada")
        
        if user_mission.status != MissionStatusEnum.IN_PROGRESS:
            self.logger.warning(
                "Misión no en progreso", 
                mission_key=mission_key, 
                status=user_mission.status
            )
            return {
                "user_id": user_id,
                "mission": {
                    "key": mission.key,
                    "title": mission.title
                },
                "status": user_mission.status.value,
                "cannot_update": True
            }
        
        # Verificar si ha expirado
        if user_mission.expires_at and user_mission.expires_at < datetime.now():
            # Marcar como expirada
            await self.mission_service.update_user_mission(
                session, user_mission.id, {
                    "status": MissionStatusEnum.EXPIRED
                }
            )
            
            self.logger.warning("Misión expirada", mission_key=mission_key)
            return {
                "user_id": user_id,
                "mission": {
                    "key": mission.key,
                    "title": mission.title
                },
                "status": MissionStatusEnum.EXPIRED.value,
                "expired": True,
                "expired_at": user_mission.expires_at.isoformat()
            }
        
        # Actualizar progreso
        current_progress = user_mission.progress or {}
        merged_progress = {**current_progress, **progress}
        
        # Si no se proporciona porcentaje, calcularlo
        if progress_percentage is None:
            # En una implementación real, esto dependería de los objetivos de la misión
            # Por ahora, usamos un valor simple basado en las claves completadas
            total_objectives = len(mission.objectives) if mission.objectives else 1
            completed_objectives = sum(
                1 for obj in merged_progress.values() 
                if obj is True or (isinstance(obj, (int, float)) and obj >= 1)
            )
            progress_percentage = (completed_objectives / total_objectives) * 100
        
        # Verificar si la misión está completa
        is_completed = progress_percentage >= 100
        
        update_data = {
            "progress": merged_progress,
            "progress_percentage": progress_percentage
        }
        
        if is_completed:
            update_data["status"] = MissionStatusEnum.COMPLETED
            update_data["completed_at"] = datetime.now()
        
        await self.mission_service.update_user_mission(
            session, user_mission.id, update_data
        )
        
        # Otorgar recompensa si se completó
        points_awarded = 0
        if is_completed and mission.points_reward > 0 and not user_mission.reward_claimed:
            # Marcar recompensa como reclamada
            await self.mission_service.update_user_mission(
                session, user_mission.id, {
                    "reward_claimed": True,
                    "reward_claimed_at": datetime.now()
                }
            )
            
            # Otorgar puntos
            result = await self.award_points(
                session, user_id, mission.points_reward, "mission",
                f"Misión completada: {mission.title}"
            )
            points_awarded = result["points_awarded"]
            
            # Si tiene un logro asociado, completarlo
            if mission.achievement_key:
                await self.complete_achievement(
                    session, user_id, mission.achievement_key
                )
        
        # Formatear respuesta
        result = {
            "user_id": user_id,
            "mission": {
                "key": mission.key,
                "title": mission.title
            },
            "previous_progress": current_progress,
            "current_progress": merged_progress,
            "progress_percentage": progress_percentage,
            "completed": is_completed,
            "completed_at": datetime.now().isoformat() if is_completed else None,
            "points_awarded": points_awarded
        }
        
        return result
    
    async def get_daily_gift(
        self, session: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """Obtiene el regalo diario para un usuario."""
        self.logger.debug("Obteniendo regalo diario", user_id=user_id)
        
        # Verificar si ya reclamó hoy
        gift_claimed = await self.check_daily_gift_claimed(session, user_id)
        
        if gift_claimed:
            self.logger.warning("Regalo diario ya reclamado", user_id=user_id)
            return {
                "user_id": user_id,
                "already_claimed": True,
                "next_available": gift_claimed["next_available"].isoformat()
            }
        
        # Determinar puntos a otorgar (en una implementación real podría variar)
        # Por ejemplo, basado en el streak de login
        points = 5.0
        
        # Otorgar puntos
        result = await self.award_points(
            session, user_id, points, "dailygift", "Regalo diario"
        )
        
        # Registrar reclamación
        # En una implementación real, esto se guardaría en la base de datos
        # Por ahora, asumimos que está implementado correctamente
        
        # Formatear respuesta
        gift_result = {
            "user_id": user_id,
            "points_awarded": points,
            "claimed_at": datetime.now().isoformat(),
            "next_available": (datetime.now() + timedelta(days=1)).isoformat()
        }
        
        return gift_result
    
    async def check_daily_gift_claimed(
        self, session: AsyncSession, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Verifica si el usuario ya reclamó su regalo diario."""
        # En una implementación real, esto consultaría la base de datos
        # Por ahora, devolvemos None para simular que no ha reclamado
        return None
    
    def calculate_level(self, points: float) -> Dict[str, Any]:
        """Calcula el nivel actual del usuario basado en sus puntos."""
        current_level = 1
        next_level = 2
        
        # Encontrar el nivel actual
        for level, data in USER_LEVELS.items():
            if points >= data["points"]:
                current_level = level
            else:
                next_level = level
                break
        
        # Obtener puntos para el siguiente nivel
        current_level_points = USER_LEVELS[current_level]["points"]
        next_level_points = USER_LEVELS[next_level]["points"] if next_level in USER_LEVELS else float("inf")
        
        # Calcular progreso
        points_range = next_level_points - current_level_points
        points_earned = points - current_level_points
        progress_percent = (points_earned / points_range) * 100 if points_range > 0 else 100
        
        # Limitar a 100%
        progress_percent = min(100, progress_percent)
        
        # Puntos para el siguiente nivel
        points_to_next_level = next_level_points - points if next_level in USER_LEVELS else 0
        
        return {
            "current_level": current_level,
            "level_name": USER_LEVELS[current_level]["name"],
            "points": points,
            "points_required": current_level_points,
            "next_level": next_level if next_level in USER_LEVELS else None,
            "next_level_points": next_level_points if next_level in USER_LEVELS else None,
            "progress_percent": progress_percent,
            "points_to_next_level": points_to_next_level
        }
    
    async def check_level_achievements(
        self, session: AsyncSession, user_id: int, level: int
    ) -> None:
        """Verifica y otorga logros relacionados con niveles."""
        # Logros de nivel (ejemplo)
        level_achievements = {
            5: "reach_level_5",
            10: "reach_level_10",
            15: "reach_level_15",
            20: "reach_level_20"
        }
        
        # Verificar si hay un logro para este nivel
        if level in level_achievements:
            achievement_key = level_achievements[level]
            await self.complete_achievement(session, user_id, achievement_key)


class PointsService(BaseService[UserPoints]):
    """Servicio para gestionar puntos de usuarios."""
    
    def __init__(self):
        super().__init__(UserPoints)
    
    async def get_user_points(
        self, session: AsyncSession, user_id: int
    ) -> Optional[UserPoints]:
        """Obtiene los puntos de un usuario."""
        self.logger.debug("Obteniendo puntos de usuario", user_id=user_id)
        
        query = select(UserPoints).where(UserPoints.user_id == user_id)
        result = await session.execute(query)
        return result.scalars().first()
    
    async def get_or_create_points(
        self, session: AsyncSession, user_id: int
    ) -> UserPoints:
        """Obtiene o crea un registro de puntos para un usuario."""
        self.logger.debug("Obteniendo o creando puntos", user_id=user_id)
        
        points = await self.get_user_points(session, user_id)
        
        if not points:
            # Crear nuevo registro
            points_data = {
                "user_id": user_id,
                "current_points": 0.0,
                "total_earned": 0.0,
                "total_spent": 0.0,
                "points_from_messages": 0.0,
                "points_from_reactions": 0.0,
                "points_from_missions": 0.0,
                "points_from_dailygift": 0.0,
                "points_from_minigames": 0.0,
                "points_from_narrative": 0.0,
                "active_multipliers": {}
            }
            
            points = await self.create(session, points_data)
        
        return points
    
    async def get_top_users(
        self, session: AsyncSession, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene los usuarios con más puntos."""
        self.logger.debug("Obteniendo usuarios top", limit=limit)
        
        # Esta consulta requiere join con tabla de usuarios
        # En una implementación real sería más compleja
        query = select(UserPoints).order_by(UserPoints.current_points.desc()).limit(limit)
        result = await session.execute(query)
        points_records = result.scalars().all()
        
        # Formatear resultados
        leaderboard = []
        for i, points in enumerate(points_records):
            # En una implementación real, aquí obtendríamos datos del usuario
            leaderboard.append({
                "rank": i + 1,
                "user_id": points.user_id,
                "points": points.current_points,
                # Otros datos del usuario como nombre, etc.
            })
        
        return leaderboard


class AchievementService(BaseService[Achievement]):
    """Servicio para gestionar logros."""
    
    def __init__(self):
        super().__init__(Achievement)
        self.user_achievement_service = UserAchievementService()
    
    async def get_by_key(
        self, session: AsyncSession, achievement_key: str
    ) -> Optional[Achievement]:
        """Obtiene un logro por su clave."""
        self.logger.debug("Obteniendo logro por clave", key=achievement_key)
        
        query = select(Achievement).where(Achievement.key == achievement_key)
        result = await session.execute(query)
        return result.scalars().first()
    
    async def get_by_category(
        self, session: AsyncSession, category: str
    ) -> List[Achievement]:
        """Obtiene logros por categoría."""
        self.logger.debug("Obteniendo logros por categoría", category=category)
        
        query = select(Achievement).where(Achievement.category == category)
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_user_achievement(
        self, session: AsyncSession, user_id: int, achievement_id: int
    ) -> Optional[UserAchievement]:
        """Obtiene un logro de usuario."""
        return await self.user_achievement_service.get_user_achievement(
            session, user_id, achievement_id
        )
    
    async def create_user_achievement(
        self, session: AsyncSession, user_achievement_data: Dict[str, Any]
    ) -> UserAchievement:
        """Crea un logro de usuario."""
        return await self.user_achievement_service.create(
            session, user_achievement_data
        )
    
    async def update_user_achievement(
        self, session: AsyncSession, user_achievement_id: int, update_data: Dict[str, Any]
    ) -> Optional[UserAchievement]:
        """Actualiza un logro de usuario."""
        return await self.user_achievement_service.update(
            session, user_achievement_id, update_data
        )
    
    async def get_user_achievements(
        self, session: AsyncSession, user_id: int
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los logros de un usuario con detalles."""
        self.logger.debug("Obteniendo logros de usuario", user_id=user_id)
        
        # En una implementación real, esto sería una consulta con join
        # Por ahora, simulamos el resultado
        
        # Obtener todos los logros
        all_achievements = await self.get_all(session)
        
        # Obtener logros del usuario
        user_achievements = await self.user_achievement_service.get_by_user(
            session, user_id
        )
        
        # Mapear logros del usuario
        user_achievement_map = {
            ua.achievement_id: ua for ua in user_achievements
        }
        
        # Combinar datos
        result = []
        for achievement in all_achievements:
            user_achievement = user_achievement_map.get(achievement.id)
            
            result.append({
                "id": achievement.id,
                "key": achievement.key,
                "name": achievement.name,
                "description": achievement.description,
                "category": achievement.category,
                "points_reward": achievement.points_reward,
                "is_hidden": achievement.is_hidden,
                "is_completed": user_achievement.is_completed if user_achievement else False,
                "progress": user_achievement.progress if user_achievement else 0.0,
                "completed_at": user_achievement.completed_at if user_achievement else None
            })
        
        return result


class UserAchievementService(BaseService[UserAchievement]):
    """Servicio para gestionar logros de usuarios."""
    
    def __init__(self):
        super().__init__(UserAchievement)
    
    async def get_user_achievement(
        self, session: AsyncSession, user_id: int, achievement_id: int
    ) -> Optional[UserAchievement]:
        """Obtiene un logro específico de un usuario."""
        self.logger.debug(
            "Obteniendo logro de usuario", 
            user_id=user_id, 
            achievement_id=achievement_id
        )
        
        query = select(UserAchievement).where(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id
            )
        )
        
        result = await session.execute(query)
        return result.scalars().first()
    
    async def get_by_user(
        self, session: AsyncSession, user_id: int
    ) -> List[UserAchievement]:
        """Obtiene todos los logros de un usuario."""
        self.logger.debug("Obteniendo logros por usuario", user_id=user_id)
        
        query = select(UserAchievement).where(UserAchievement.user_id == user_id)
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_completed_achievements(
        self, session: AsyncSession, user_id: int
    ) -> List[UserAchievement]:
        """Obtiene los logros completados de un usuario."""
        self.logger.debug("Obteniendo logros completados", user_id=user_id)
        
        query = select(UserAchievement).where(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.is_completed == True
            )
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())


class MissionService(BaseService[Mission]):
    """Servicio para gestionar misiones."""
    
    def __init__(self):
        super().__init__(Mission)
        self.user_mission_service = UserMissionService()
    
    async def get_by_key(
        self, session: AsyncSession, mission_key: str
    ) -> Optional[Mission]:
        """Obtiene una misión por su clave."""
        self.logger.debug("Obteniendo misión por clave", key=mission_key)
        
        query = select(Mission).where(Mission.key == mission_key)
        result = await session.execute(query)
        return result.scalars().first()
    
    async def get_by_type(
        self, session: AsyncSession, mission_type: MissionTypeEnum
    ) -> List[Mission]:
        """Obtiene misiones por tipo."""
        self.logger.debug("Obteniendo misiones por tipo", type=mission_type)
        
        query = select(Mission).where(
            and_(
                Mission.mission_type == mission_type,
                Mission.is_active == True
            )
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_available_missions(
        self, session: AsyncSession, user_id: int, mission_type: Optional[MissionTypeEnum] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene misiones disponibles para un usuario."""
        self.logger.debug(
            "Obteniendo misiones disponibles", 
            user_id=user_id, 
            mission_type=mission_type
        )
        
        # Construir query base
        query = select(Mission).where(Mission.is_active == True)
        
        # Filtrar por tipo si se especifica
        if mission_type:
            query = query.where(Mission.mission_type == mission_type)
        
        # Obtener todas las misiones activas
        result = await session.execute(query)
        missions = result.scalars().all()
        
        # Obtener misiones del usuario
        user_missions = await self.user_mission_service.get_by_user(session, user_id)
        
        # Crear mapa de misiones de usuario
        user_mission_map = {
            um.mission_id: um for um in user_missions
        }
        
        # Filtrar misiones disponibles
        available_missions = []
        for mission in missions:
            user_mission = user_mission_map.get(mission.id)
            
            # Verificar disponibilidad
            is_available = True
            status = None
            
            if user_mission:
                status = user_mission.status
                
                # Si es una misión única y ya está completada, no está disponible
                if mission.mission_type == MissionTypeEnum.ONE_TIME and user_mission.status == MissionStatusEnum.COMPLETED:
                    is_available = False
                
                # Si es una misión diaria/semanal y ya está completada hoy/esta semana, no está disponible
                if mission.mission_type in [MissionTypeEnum.DAILY, MissionTypeEnum.WEEKLY] and user_mission.status == MissionStatusEnum.COMPLETED:
                    # Verificar si fue completada recientemente
                    if user_mission.completed_at:
                        if mission.mission_type == MissionTypeEnum.DAILY:
                            # Si fue completada hoy, no está disponible
                            if (datetime.now() - user_mission.completed_at).days < 1:
                                is_available = False
                        elif mission.mission_type == MissionTypeEnum.WEEKLY:
                            # Si fue completada esta semana, no está disponible
                            if (datetime.now() - user_mission.completed_at).days < 7:
                                is_available = False
                
                # Si está en progreso, está disponible
                if user_mission.status == MissionStatusEnum.IN_PROGRESS:
                    is_available = True
            
            if is_available:
                available_missions.append({
                    "id": mission.id,
                    "key": mission.key,
                    "title": mission.title,
                    "description": mission.description,
                    "mission_type": mission.mission_type.value,
                    "category": mission.category,
                    "points_reward": mission.points_reward,
                    "status": status.value if status else None,
                    "is_new": user_mission is None
                })
        
        return available_missions
    
    async def get_user_mission(
        self, session: AsyncSession, user_id: int, mission_id: int
    ) -> Optional[UserMission]:
        """Obtiene una misión específica de un usuario."""
        return await self.user_mission_service.get_user_mission(
            session, user_id, mission_id
        )
    
    async def create_user_mission(
        self, session: AsyncSession, user_mission_data: Dict[str, Any]
    ) -> UserMission:
        """Crea una misión de usuario."""
        return await self.user_mission_service.create(
            session, user_mission_data
        )
    
    async def update_user_mission(
        self, session: AsyncSession, user_mission_id: int, update_data: Dict[str, Any]
    ) -> Optional[UserMission]:
        """Actualiza una misión de usuario."""
        return await self.user_mission_service.update(
            session, user_mission_id, update_data
        )
    
    async def get_active_missions(
        self, session: AsyncSession, user_id: int
    ) -> List[Dict[str, Any]]:
        """Obtiene las misiones activas de un usuario."""
        self.logger.debug("Obteniendo misiones activas", user_id=user_id)
        
        # Obtener misiones del usuario que estén en progreso
        user_missions = await self.user_mission_service.get_active_missions(
            session, user_id
        )
        
        # Formatear resultado
        result = []
        for um in user_missions:
            # En una implementación real, haríamos join con la tabla de misiones
            # Por ahora, simulamos el resultado
            mission = await self.get_by_id(session, um.mission_id)
            
            if mission:
                result.append({
                    "id": um.id,
                    "mission_id": mission.id,
                    "key": mission.key,
                    "title": mission.title,
                    "description": mission.description,
                    "mission_type": mission.mission_type.value,
                    "category": mission.category,
                    "status": um.status.value,
                    "progress_percentage": um.progress_percentage,
                    "started_at": um.started_at.isoformat() if um.started_at else None,
                    "expires_at": um.expires_at.isoformat() if um.expires_at else None
                })
        
        return result


class UserMissionService(BaseService[UserMission]):
    """Servicio para gestionar misiones de usuarios."""
    
    def __init__(self):
        super().__init__(UserMission)
    
    async def get_user_mission(
        self, session: AsyncSession, user_id: int, mission_id: int
    ) -> Optional[UserMission]:
        """Obtiene una misión específica de un usuario."""
        self.logger.debug(
            "Obteniendo misión de usuario", 
            user_id=user_id, 
            mission_id=mission_id
        )
        
        query = select(UserMission).where(
            and_(
                UserMission.user_id == user_id,
                UserMission.mission_id == mission_id
            )
        )
        
        result = await session.execute(query)
        return result.scalars().first()
    
    async def get_by_user(
        self, session: AsyncSession, user_id: int
    ) -> List[UserMission]:
        """Obtiene todas las misiones de un usuario."""
        self.logger.debug("Obteniendo misiones por usuario", user_id=user_id)
        
        query = select(UserMission).where(UserMission.user_id == user_id)
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_active_missions(
        self, session: AsyncSession, user_id: int
    ) -> List[UserMission]:
        """Obtiene las misiones activas de un usuario."""
        self.logger.debug("Obteniendo misiones activas", user_id=user_id)
        
        query = select(UserMission).where(
            and_(
                UserMission.user_id == user_id,
                UserMission.status.in_([
                    MissionStatusEnum.AVAILABLE, 
                    MissionStatusEnum.IN_PROGRESS
                ])
            )
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_completed_missions(
        self, session: AsyncSession, user_id: int
    ) -> List[UserMission]:
        """Obtiene las misiones completadas de un usuario."""
        self.logger.debug("Obteniendo misiones completadas", user_id=user_id)
        
        query = select(UserMission).where(
            and_(
                UserMission.user_id == user_id,
                UserMission.status == MissionStatusEnum.COMPLETED
            )
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())