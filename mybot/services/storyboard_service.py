from sqlalchemy import select, delete, update
from database.setup import get_session
from database.models import Storyboard

class StoryboardService:

    @staticmethod
    async def create_scene(scene_id: str):
        async with get_session() as session:
            scene = Storyboard(scene_id=scene_id, order=0, character='', dialogue='', media_type='text')
            session.add(scene)
            await session.commit()

    @staticmethod
    async def add_dialogue(scene_id, order, character, dialogue, media_type, media_path=None, condition=None):
        async with get_session() as session:
            dialogue_entry = Storyboard(
                scene_id=scene_id,
                order=order,
                character=character,
                dialogue=dialogue,
                media_type=media_type,
                media_path=media_path,
                condition=condition
            )
            session.add(dialogue_entry)
            await session.commit()

    @staticmethod
    async def edit_dialogue(dialogue_id, **kwargs):
        async with get_session() as session:
            await session.execute(update(Storyboard).where(Storyboard.id == dialogue_id).values(**kwargs))
            await session.commit()

    @staticmethod
    async def delete_dialogue(dialogue_id):
        async with get_session() as session:
            await session.execute(delete(Storyboard).where(Storyboard.id == dialogue_id))
            await session.commit()

    @staticmethod
    async def get_scene_dialogues(scene_id):
        async with get_session() as session:
            result = await session.execute(select(Storyboard).where(Storyboard.scene_id == scene_id).order_by(Storyboard.order))
            return result.scalars().all()

    @staticmethod
    async def get_all_scenes():
        async with get_session() as session:
            result = await session.execute(select(Storyboard.scene_id).distinct())
            return [row[0] for row in result.all()]
