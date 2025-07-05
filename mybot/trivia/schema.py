from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

class TriviaType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    OPEN_TEXT = "open_text"
    SEQUENCE = "sequence"
    TIMED_CHALLENGE = "timed_challenge"
    PROGRESSIVE = "progressive"

class TriggerEvent(Enum):
    LEVEL_UP = "level_up"
    POINTS_MILESTONE = "points_milestone"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"
    TIME_BASED = "time_based"
    STORY_COMPLETION = "story_completion"
    BOSS_DEFEAT = "boss_defeat"
    SPECIAL_ACTION = "special_action"
    RANDOM_ENCOUNTER = "random_encounter"

class RewardType(Enum):
    POINTS = "points"
    LEVEL_BOOST = "level_boost"
    SPECIAL_CONTENT = "special_content"
    STORYBOARD_UNLOCK = "storyboard_unlock"
    ACHIEVEMENT = "achievement"
    ITEM = "item"
    ACCESS_PRIVILEGE = "access_privilege"

@dataclass
class TriviaReward:
    type: RewardType
    value: Union[int, str, Dict[str, Any]]
    condition: str
    immediate: bool = True
    unlock_requirements: Optional[Dict[str, Any]] = None

@dataclass
class TriviaQuestion:
    id: str
    question: str
    question_type: TriviaType
    options: Optional[List[str]] = None
    correct_answer: Union[str, int, List[str], None] = None
    explanation: Optional[str] = None
    difficulty: int = 1
    time_limit: Optional[int] = None
    media_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)

@dataclass
class TriviaSession:
    id: str
    user_id: int
    channel_id: int
    questions: List[TriviaQuestion]
    current_question_index: int = 0
    score: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    time_limit: Optional[int] = None
    rewards_on_correct: List[TriviaReward] = field(default_factory=list)
    rewards_on_wrong: List[TriviaReward] = field(default_factory=list)
    rewards_on_completion: List[TriviaReward] = field(default_factory=list)
    triggered_by: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TriviaTemplate:
    id: str
    name: str
    description: str
    trigger_events: List[TriggerEvent]
    trigger_conditions: Dict[str, Any]
    question_pool: List[str]
    selection_strategy: str
    max_questions: int = 5
    min_score_percentage: float = 0.6
    rewards: Dict[str, List[TriviaReward]] = field(default_factory=dict)
    unlock_storyboards: List[str] = field(default_factory=list)
    special_content_unlocks: List[str] = field(default_factory=list)
