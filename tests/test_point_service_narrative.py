import asyncio
import sys
import types
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import importlib.util
from pathlib import Path

# Provide dummy 'database' module to satisfy imports in service modules
database_module = types.ModuleType("database")
database_models = types.ModuleType("database.models")
for name in [
    "Achievement",
    "UserAchievement",
    "InviteToken",
    "VipSubscription",
    "Badge",
    "UserBadge",
    "UserStats",
    "User",
    "UserMissionEntry",
]:
    setattr(database_models, name, type(name, (), {}))
database_module.models = database_models
sys.modules.setdefault("database", database_module)
sys.modules.setdefault("database.models", database_models)

# Create lightweight 'services' package with required modules
services_pkg = types.ModuleType("services")
sys.modules.setdefault("services", services_pkg)

# Minimal 'utils.user_roles' module
utils_pkg = types.ModuleType("utils")
user_roles_mod = types.ModuleType("utils.user_roles")
def _dummy_get_points_multiplier(bot, user_id, session=None):
    return 1
user_roles_mod.get_points_multiplier = AsyncMock(return_value=1)
utils_pkg.user_roles = user_roles_mod
sys.modules.setdefault("utils", utils_pkg)
sys.modules.setdefault("utils.user_roles", user_roles_mod)

ROOT = Path(__file__).resolve().parents[1]

# Load real narrative_engine module
spec_ne = importlib.util.spec_from_file_location(
    "services.narrative_engine", ROOT / "mybot/services/narrative_engine.py"
)
narrative_module = importlib.util.module_from_spec(spec_ne)
spec_ne.loader.exec_module(narrative_module)
sys.modules["services.narrative_engine"] = narrative_module
services_pkg.narrative_engine = narrative_module

# Stub other service modules
for mod_name in ["level_service", "achievement_service", "event_service"]:
    mod = types.ModuleType(f"services.{mod_name}")
    setattr(mod, mod_name.split("_")[0].capitalize() + "Service", type("Dummy", (), {}))
    sys.modules[f"services.{mod_name}"] = mod
    setattr(services_pkg, mod_name, mod)

# Dynamically load point_service module without importing mybot.services
spec_ps = importlib.util.spec_from_file_location(
    "point_service", ROOT / "mybot/services/point_service.py"
)
point_service_module = importlib.util.module_from_spec(spec_ps)
spec_ps.loader.exec_module(point_service_module)
sys.modules.setdefault("point_service", point_service_module)
PointService = point_service_module.PointService
TriggerType = narrative_module.TriggerType

class DummyProgress:
    def __init__(self):
        self.last_activity_at = None
        self.messages_sent = 0


@pytest.mark.asyncio
async def test_award_message_triggers_narrative(monkeypatch):
    session = MagicMock()
    session.commit = AsyncMock()

    narrative_engine = MagicMock()
    narrative_engine.process_event = AsyncMock()

    service = PointService(session, narrative_engine=narrative_engine)

    monkeypatch.setattr(service, '_get_or_create_progress', AsyncMock(return_value=DummyProgress()))
    monkeypatch.setattr(service, 'add_points', AsyncMock(return_value=DummyProgress()))

    ach_service = MagicMock()
    ach_service.check_message_achievements = AsyncMock()
    ach_service.check_user_badges = AsyncMock(return_value=[])
    ach_service.award_badge = AsyncMock()
    with patch('point_service.AchievementService', return_value=ach_service):
        await service.award_message(1, bot=None, channel_id=10)

    narrative_engine.process_event.assert_called_once()
    event = narrative_engine.process_event.call_args.args[0]
    assert event.user_id == 1
    assert event.trigger_type == TriggerType.POINTS_GAINED
    assert event.data == {'points': 1, 'source': 'message', 'channel_id': 10}


@pytest.mark.asyncio
async def test_award_reaction_triggers_narrative(monkeypatch):
    session = MagicMock()
    session.commit = AsyncMock()

    narrative_engine = MagicMock()
    narrative_engine.process_event = AsyncMock()

    service = PointService(session, narrative_engine=narrative_engine)

    monkeypatch.setattr(service, 'add_points', AsyncMock(return_value=DummyProgress()))

    ach_service = MagicMock()
    ach_service.check_user_badges = AsyncMock(return_value=[])
    ach_service.award_badge = AsyncMock()
    with patch('point_service.AchievementService', return_value=ach_service):
        user = MagicMock(id=2)
        await service.award_reaction(user, message_id=99, bot=None, channel_id=20, reaction_emoji='\u2764')

    narrative_engine.process_event.assert_called_once()
    event = narrative_engine.process_event.call_args.args[0]
    assert event.user_id == 2
    assert event.trigger_type == TriggerType.REACTION
    assert event.data == {'emoji': '\u2764', 'points': 0.5, 'channel_id': 20}
