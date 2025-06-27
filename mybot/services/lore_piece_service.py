from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import LorePiece

class LorePieceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def code_exists(self, code_name: str) -> bool:
        stmt = select(LorePiece).where(LorePiece.code_name == code_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_lore_piece(
        self,
        code_name: str,
        title: str,
        content_type: str,
        content: str,
        *,
        description: str | None = None,
        category: str | None = None,
        is_main_story: bool = False,
    ) -> LorePiece:
        piece = LorePiece(
            code_name=code_name,
            title=title,
            description=description,
            content_type=content_type,
            content=content,
            category=category,
            is_main_story=is_main_story,
        )
        self.session.add(piece)
        await self.session.commit()
        await self.session.refresh(piece)
        return piece
