from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Channel
from utils.text_utils import sanitize_text


class ChannelService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_channel(self, chat_id: int, title: str | None = None) -> Channel:
        channel = await self.session.get(Channel, chat_id)
        clean_title = sanitize_text(title) if title is not None else None
        if channel:
            if clean_title:
                channel.title = clean_title
        else:
            channel = Channel(id=chat_id, title=clean_title)
            self.session.add(channel)
        await self.session.commit()
        await self.session.refresh(channel)
        return channel

    async def set_reactions(
        self, chat_id: int, reactions: list[str], points: list[float] | None = None
    ) -> Channel:
        channel = await self.session.get(Channel, chat_id)
        if not channel:
            channel = Channel(id=chat_id)
            self.session.add(channel)
        channel.reactions = reactions
        if points is not None:
            channel.reaction_points = [float(p) for p in points]
        await self.session.commit()
        await self.session.refresh(channel)
        return channel

    async def get_reactions(self, chat_id: int) -> list[str]:
        """Return raw reaction texts configured for the channel."""
        channel = await self.session.get(Channel, chat_id)
        if channel and channel.reactions:
            try:
                reactions = [str(r).strip() for r in channel.reactions if str(r).strip()]
                if reactions:
                    return reactions[:10]
            except (TypeError, ValueError):
                pass
        from utils.config import DEFAULT_REACTION_BUTTONS

        return DEFAULT_REACTION_BUTTONS

    async def get_reaction_points(self, chat_id: int) -> list[float]:
        channel = await self.session.get(Channel, chat_id)
        if channel and channel.reaction_points:
            try:
                points = [float(p) for p in channel.reaction_points]
                return points[:10]
            except (TypeError, ValueError):
                pass
        reactions = await self.get_reactions(chat_id)
        return [0.5] * len(reactions)

    async def list_channels(self) -> list[Channel]:
        result = await self.session.execute(select(Channel))
        return list(result.scalars().all())

    async def remove_channel(self, chat_id: int) -> None:
        channel = await self.session.get(Channel, chat_id)
        if channel:
            await self.session.delete(channel)
            await self.session.commit()
