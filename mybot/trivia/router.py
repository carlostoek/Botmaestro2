from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext

from .manager import TriviaManager
from states.trivia_states import TriviaStates

router = Router()

@router.callback_query(F.data.startswith("trivia_answer_"), StateFilter(TriviaStates.waiting_answer))
async def handle_trivia_answer(callback: CallbackQuery, state: FSMContext, trivia_manager: TriviaManager):
    answer = callback.data.split("trivia_answer_")[1]
    await trivia_manager.process_answer(callback.from_user.id, answer, state)
    await callback.answer()

@router.message(StateFilter(TriviaStates.waiting_answer))
async def handle_text_answer(message: Message, state: FSMContext, trivia_manager: TriviaManager):
    await trivia_manager.process_answer(message.from_user.id, message.text, state)
