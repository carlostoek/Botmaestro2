import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mybot.database.setup import get_session, init_db
from mybot.database.narrative_models import NarrativeFragment, NarrativeDecision
from scripts.story_content import STORY_GRAPH

async def populate_narrative_data(session: AsyncSession):
    """
    Clears and populates the narrative tables from STORY_GRAPH.
    """
    print("Clearing old narrative data...")
    await session.execute(NarrativeDecision.__table__.delete())
    await session.execute(NarrativeFragment.__table__.delete())
    
    print("Populating narrative fragments...")
    fragments = {}
    for key, data in STORY_GRAPH.items():
        fragment = NarrativeFragment(
            key=key,
            text=data['text'],
            character=data.get('character', 'Lucien')
        )
        session.add(fragment)
        fragments[key] = fragment
    
    await session.flush() # Flush to get fragment IDs

    print("Populating narrative decisions...")
    for key, data in STORY_GRAPH.items():
        fragment = fragments[key]
        for decision_data in data.get('decisions', []):
            decision = NarrativeDecision(
                fragment_id=fragment.id,
                text=decision_data['text'],
                next_fragment_key=decision_data['next']
            )
            session.add(decision)

    await session.commit()
    print("Narrative data populated successfully.")

async def main():
    await init_db()
    Session = await get_session()
    async with Session() as session:
        await populate_narrative_data(session)

if __name__ == "__main__":
    asyncio.run(main())