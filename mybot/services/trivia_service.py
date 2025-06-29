import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import TriviaQuestion, TriviaResult
from services.point_service import PointService
from backpack import desbloquear_pista_narrativa


def parse_options_from_db(options_field) -> list[str]:
    if isinstance(options_field, list):
        return options_field
    if isinstance(options_field, str):
        try:
            import json
            return json.loads(options_field)
        except Exception:
            return [opt.strip() for opt in options_field.split("|") if opt.strip()]
    return []


class TriviaService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_random_trivia_question(self, user_id: int) -> TriviaQuestion | None:
        stmt = select(TriviaQuestion)
        result = await self.session.execute(stmt)
        questions = result.scalars().all()
        if not questions:
            return None
        answered_stmt = select(TriviaResult.question_id).where(
            TriviaResult.user_id == user_id, TriviaResult.is_correct == True
        )
        answered = await self.session.execute(answered_stmt)
        answered_ids = {row[0] for row in answered.all()}
        available = [q for q in questions if q.id not in answered_ids]
        if not available:
            return None
        return random.choice(available)

    async def record_trivia_result(self, user_id: int, question_id: int, is_correct: bool) -> TriviaResult:
        result = TriviaResult(user_id=user_id, question_id=question_id, is_correct=is_correct)
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def get_trivia_attempts(self, user_id: int, question_id: int) -> int:
        stmt = select(func.count(TriviaResult.id)).where(
            TriviaResult.user_id == user_id, TriviaResult.question_id == question_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def check_if_trivia_answered_correctly(self, user_id: int, question_id: int) -> bool:
        stmt = select(TriviaResult).where(
            TriviaResult.user_id == user_id,
            TriviaResult.question_id == question_id,
            TriviaResult.is_correct == True,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def handle_correct_answer(self, user_id: int, question: TriviaQuestion, bot=None):
        await PointService(self.session).add_points(user_id, question.points, bot=bot)
        if question.unlocks:
            await desbloquear_pista_narrativa(bot, user_id, question.unlocks, {"source": "trivia"})

    async def handle_incorrect_answer(self, user_id: int, question_id: int):
        await self.record_trivia_result(user_id, question_id, False)


import logging
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.sql import func
from aiogram import Bot
from database.models import TriviaQuestion, TriviaResult, User, LorePiece
from services import point_service
from utils import messages
import json

try:
    from backpack import desbloquear_pista_narrativa
except ImportError:
    logging.warning("backpack.desbloquear_pista_narrativa no encontrada. Aseg\u00farate de que la funci\u00f3n exista o ad\u00e1ptala.")
    async def desbloquear_pista_narrativa(session, user_id, lore_piece_code):
        logging.warning(f"Funci\u00f3n desbloquear_pista_narrativa NO implementada. No se desbloquear\u00e1 la pista {lore_piece_code} para {user_id}.")
        return None

logger = logging.getLogger(__name__)

ALLOW_RETRY_ON_INCORRECT = True
MAX_INCORRECT_ATTEMPTS = 3

async def get_random_trivia_question(session: AsyncSession, user_id: int, mission_id: str = None) -> TriviaQuestion | None:
    answered_correctly_subquery = select(TriviaResult.question_id).where(
        TriviaResult.user_id == user_id,
        TriviaResult.is_correct == True
    ).scalar_subquery()

    query = select(TriviaQuestion).where(
        TriviaQuestion.id.notin_(answered_correctly_subquery)
    )

    if mission_id:
        query = query.where(TriviaQuestion.mission_required == mission_id)
        logger.info(f"Buscando trivias para misi\u00f3n: {mission_id}")

    result = await session.execute(query)
    available_trivias = result.scalars().all()

    if not available_trivias:
        logger.info(f"No hay trivias disponibles para el usuario {user_id} (misi\u00f3n: {mission_id}).")
        return None

    selected_trivia = random.choice(available_trivias)
    logger.info(f"Trivia seleccionada para usuario {user_id}: {selected_trivia.id} - {selected_trivia.question[:30]}...")
    return selected_trivia

async def record_trivia_result(session: AsyncSession, user_id: int, question_id: int, is_correct: bool):
    trivia_result = TriviaResult(
        user_id=user_id,
        question_id=question_id,
        is_correct=is_correct
    )
    session.add(trivia_result)
    await session.commit()
    logger.info(f"Resultado de trivia registrado para usuario {user_id}, pregunta {question_id}: Correcta={is_correct}")

async def get_trivia_attempts(session: AsyncSession, user_id: int, question_id: int) -> int:
    stmt = select(func.count()).where(
        TriviaResult.user_id == user_id,
        TriviaResult.question_id == question_id
    )
    result = await session.execute(stmt)
    return result.scalar_one()

async def check_if_trivia_answered_correctly(session: AsyncSession, user_id: int, question_id: int) -> bool:
    stmt = select(TriviaResult).where(
        TriviaResult.user_id == user_id,
        TriviaResult.question_id == question_id,
        TriviaResult.is_correct == True
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None

async def handle_correct_answer(session: AsyncSession, user_id: int, question_id: int, bot: Bot) -> str:
    question = await session.get(TriviaQuestion, question_id)
    if not question:
        logger.error(f"Pregunta de trivia {question_id} no encontrada al manejar respuesta correcta.")
        return messages.TRIVIA_NO_MORE_AVAILABLE

    if question.points > 0:
        await point_service.PointService(session).add_points(user_id, question.points, bot=bot)
        logger.info(f"Usuario {user_id} gan\u00f3 {question.points} puntos por trivia {question_id}.")

    await record_trivia_result(session, user_id, question_id, is_correct=True)

    unlocked_item_description = ""
    if question.exclusive_content and question.unlocks:
        if question.unlocks.startswith("LORE_PIECE_"):
            lore_piece_code = question.unlocks
            lore_piece = await desbloquear_pista_narrativa(bot, user_id, lore_piece_code)
            if lore_piece:
                unlocked_item_description = f"Pista: '{lore_piece.title}'"
            else:
                logger.warning(f"No se pudo desbloquear la pista {lore_piece_code} para usuario {user_id}.")
                unlocked_item_description = "un misterioso elemento"
        elif question.unlocks.startswith("NARRATIVE_DOOR_"):
            user = await session.get(User, user_id)
            if user:
                if 'narrative_progress' not in user.achievements:
                    user.achievements['narrative_progress'] = {}
                user.achievements['narrative_progress'][question.unlocks] = True
                await session.commit()
                unlocked_item_description = f"Acceso a: '{question.unlocks.replace('NARRATIVE_DOOR_', 'Puerta Narrativa ')}'"
            else:
                unlocked_item_description = "algo inesperado"
            logger.info(f"Usuario {user_id} desbloque\u00f3 {question.unlocks} por trivia {question_id}.")

        return messages.TRIVIA_EXCLUSIVE_CONTENT_UNLOCKED.format(unlocked_item=unlocked_item_description)

    if question.points > 0:
        return messages.TRIVIA_CORRECT_ANSWER.format(points=question.points)
    else:
        return messages.TRIVIA_POINTS_ONLY.format(points=0)

async def handle_incorrect_answer(session: AsyncSession, user_id: int, question_id: int) -> str:
    await record_trivia_result(session, user_id, question_id, is_correct=False)

    current_attempts = await get_trivia_attempts(session, user_id, question_id)

    if ALLOW_RETRY_ON_INCORRECT and current_attempts < MAX_INCORRECT_ATTEMPTS:
        sarcastic_message = random.choice(messages.TRIVIA_INCORRECT_ANSWER_SARCASTIC)
        return sarcastic_message + "\n\n" + messages.TRIVIA_RETRY_PROMPT
    else:
        return messages.TRIVIA_NO_RETRY_ALLOWED

def parse_options_from_db(options_data: str | list) -> list[str]:
    if isinstance(options_data, list):
        return options_data
    if isinstance(options_data, str):
        try:
            return json.loads(options_data)
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar opciones JSON: {options_data}")
            return []
    logger.error(f"Tipo de opciones inesperado: {type(options_data)}")
    return []

