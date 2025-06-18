import asyncio

from mybot.database.setup import init_db, get_session
from mybot.services.achievement_service import AchievementService
from mybot.services.level_service import LevelService
from mybot.services.mission_service import MissionService

DEFAULT_MISSIONS = [
    {
        "name": "Daily Check-in",
        "description": "Registra tu actividad diaria con /checkin",
        "reward_points": 10,
        "mission_type": "login_streak",
        "target_value": 1,
        "duration_days": 0,
        "category": "standard",
        "user_type": "all",
        "order_priority": 0,
    },
    {
        "name": "Primer Mensaje",
        "description": "Envía tu primer mensaje en el chat",
        "reward_points": 5,
        "mission_type": "messages",
        "target_value": 1,
        "duration_days": 0,
        "category": "standard",
        "user_type": "all",
        "order_priority": 0,
    },
]

# VIP Onboarding missions
VIP_ONBOARDING_MISSIONS = [
    {
        "name": "Bienvenida VIP",
        "description": "¡Bienvenido al VIP! Explora tu nuevo estatus premium",
        "reward_points": 50,
        "mission_type": "one_time",
        "target_value": 1,
        "duration_days": 0,
        "category": "vip_onboarding",
        "user_type": "vip",
        "order_priority": 1,
    },
    {
        "name": "Primer Check-in VIP",
        "description": "Realiza tu primer check-in como miembro VIP",
        "reward_points": 20,
        "mission_type": "one_time",
        "target_value": 1,
        "duration_days": 0,
        "category": "vip_onboarding",
        "user_type": "vip",
        "order_priority": 2,
    },
    {
        "name": "Explorar Recompensas VIP",
        "description": "Visita la sección de recompensas VIP",
        "reward_points": 15,
        "mission_type": "one_time",
        "target_value": 1,
        "duration_days": 0,
        "category": "vip_onboarding",
        "user_type": "vip",
        "order_priority": 3,
    },
    {
        "name": "Primera Interacción VIP",
        "description": "Envía tu primer mensaje como miembro VIP",
        "reward_points": 30,
        "mission_type": "one_time",
        "target_value": 1,
        "duration_days": 0,
        "category": "vip_onboarding",
        "user_type": "vip",
        "order_priority": 4,
    },
]

# Free Onboarding missions
FREE_ONBOARDING_MISSIONS = [
    {
        "name": "Primeros Pasos",
        "description": "¡Bienvenido! Comienza tu aventura aquí",
        "reward_points": 10,
        "mission_type": "one_time",
        "target_value": 1,
        "duration_days": 0,
        "category": "free_onboarding",
        "user_type": "free",
        "order_priority": 1,
    },
    {
        "name": "Primer Mensaje",
        "description": "Envía tu primer mensaje en el chat",
        "reward_points": 5,
        "mission_type": "one_time",
        "target_value": 1,
        "duration_days": 0,
        "category": "free_onboarding",
        "user_type": "free",
        "order_priority": 2,
    },
    {
        "name": "Explorar Perfil",
        "description": "Visita tu perfil para ver tu progreso",
        "reward_points": 5,
        "mission_type": "one_time",
        "target_value": 1,
        "duration_days": 0,
        "category": "free_onboarding",
        "user_type": "free",
        "order_priority": 3,
    },
]

async def main() -> None:
    await init_db()
    Session = await get_session()
    async with Session() as session:
        await AchievementService(session).ensure_achievements_exist()
        level_service = LevelService(session)
        await level_service._init_levels()

        mission_service = MissionService(session)
        existing = await mission_service.get_active_missions()
        
        if not existing:
            print("Creating default missions...")
            all_missions = DEFAULT_MISSIONS + VIP_ONBOARDING_MISSIONS + FREE_ONBOARDING_MISSIONS
            
            for m in all_missions:
                await mission_service.create_mission(
                    m["name"],
                    m["description"],
                    m["mission_type"],
                    m.get("target_value", 1),
                    m["reward_points"],
                    m.get("duration_days", 0),
                    m.get("category", "standard"),
                    m.get("user_type", "all"),
                    m.get("order_priority", 0),
                )
                print(f"Created mission: {m['name']} (Category: {m.get('category', 'standard')})")
        else:
            print(f"Found {len(existing)} existing missions, skipping creation.")
            
    print("Database initialised with onboarding system")

if __name__ == "__main__":
    asyncio.run(main())