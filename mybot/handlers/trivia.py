from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from services.trivia_service import TriviaService
from utils.messages import BOT_MESSAGES

router = Router()


@router.message(F.text.startswith('/trivia'))
async def trivia_command(message: Message, session: AsyncSession):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer('Debes indicar el código de la trivia. Uso: /trivia <codigo>')
        return
    code = parts[1].strip()
    service = TriviaService(session)
    trivia = await service.get_trivia_by_code(code)
    if not trivia:
        await message.answer('Trivia no encontrada.')
        return
    buttons = [
        [InlineKeyboardButton(text=opt, callback_data=f'trivia_ans:{trivia.id}:{i}')]
        for i, opt in enumerate(trivia.options)
    ]
    await message.answer(trivia.question, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith('trivia_ans:'))
async def trivia_answer(callback: CallbackQuery, session: AsyncSession, bot):
    _, tid, idx = callback.data.split(':')
    trivia_service = TriviaService(session)
    trivia = await trivia_service.get_trivia_by_id(int(tid))
    if not trivia:
        return await callback.answer('Trivia no disponible', show_alert=True)
    correct = await trivia_service.answer_trivia(callback.from_user.id, trivia, int(idx), bot=bot)
    if correct:
        text = BOT_MESSAGES.get('trivia_correct', '¡Correcto!')
    else:
        text = BOT_MESSAGES.get('trivia_wrong', 'Respuesta incorrecta.')
    await callback.message.edit_text(text)
    await callback.answer()
