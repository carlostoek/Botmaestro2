from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..database.models import User
from ..database.narrative_models import NarrativeFragment, NarrativeDecision, UserNarrativeState, UserDecisionLog

class NarrativeService:
    def __init__(self, session: AsyncSession, user_service=None, point_service=None, backpack_service=None):
        self.session = session
        self.user_service = user_service
        self.point_service = point_service
        self.backpack_service = backpack_service

    async def get_user_current_fragment(self, user_id: int):
        """
        Gets the current story fragment for a user.
        If they haven't started, returns the initial fragment.
        """
        user_state = await self.session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        user_state = user_state.scalar_one_or_none()

        fragment_key = 'start'
        if user_state and user_state.current_fragment_key:
            fragment_key = user_state.current_fragment_key
        
        fragment = await self.session.execute(
            select(NarrativeFragment).where(NarrativeFragment.key == fragment_key)
        )
        fragment = fragment.scalar_one_or_none()

        if not fragment: # Fallback if fragment key in state is invalid
            fragment_key = 'start'
            fragment = await self.session.execute(
                select(NarrativeFragment).where(NarrativeFragment.key == fragment_key)
            )
            fragment = fragment.scalar_one_or_none()

        if not user_state:
            user_state = UserNarrativeState(user_id=user_id, current_fragment_key=fragment_key)
            self.session.add(user_state)
            await self.session.commit()
            await self.session.refresh(user_state)
        elif user_state.current_fragment_key != fragment_key:
            user_state.current_fragment_key = fragment_key
            await self.session.commit()
            await self.session.refresh(user_state)
            
        return fragment

    async def process_user_decision(self, user_id: int, decision_id: int):
        """
        Processes a decision, checks conditions, and advances the story.
        """
        decision = await self.session.execute(
            select(NarrativeDecision).where(NarrativeDecision.id == decision_id)
        )
        decision = decision.scalar_one_or_none()

        if not decision:
            return None # Decision not found

        # Check conditions (placeholder for now)
        # if not await self.check_conditions(user_id, decision):
        #     return None # Conditions not met

        # Log the decision
        user_decision_log = UserDecisionLog(user_id=user_id, decision_id=decision.id)
        self.session.add(user_decision_log)

        # Update user's narrative state
        user_state = await self.session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        user_state = user_state.scalar_one_or_none()

        if user_state:
            user_state.current_fragment_key = decision.next_fragment_key
        else:
            user_state = UserNarrativeState(user_id=user_id, current_fragment_key=decision.next_fragment_key)
            self.session.add(user_state)
        
        await self.session.commit()
        await self.session.refresh(user_state)

        # Fetch and return the new fragment
        new_fragment = await self.session.execute(
            select(NarrativeFragment).where(NarrativeFragment.key == decision.next_fragment_key)
        )
        return new_fragment.scalar_one_or_none()

    async def check_conditions(self, user_id: int, decision: NarrativeDecision) -> bool:
        """
        Helper function to check all conditions for a decision.
        This will need access to other services (user, points, backpack).
        """
        # For now, always return True. Implement actual condition checking later.
        return True