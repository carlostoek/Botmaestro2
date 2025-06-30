from __future__ import annotations

from aiogram import Bot
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .schema import TriviaSession, TriviaType


class TriviaContentDelivery:
    @staticmethod
    async def send_trivia_intro(bot: Bot, session: TriviaSession):
        text = f"\U0001F3AF {session.triggered_by}"
        builder = InlineKeyboardBuilder()
        builder.button(text="\u2728 Comenzar", callback_data="trivia_start")
        builder.button(text="Cancelar", callback_data="trivia_cancel")
        await bot.send_message(session.user_id, text, reply_markup=builder.as_markup())

    @staticmethod
    async def send_question(bot: Bot, session: TriviaSession):
        question = session.questions[session.current_question_index]
        text = question.question
        builder = InlineKeyboardBuilder()
        if question.question_type == TriviaType.MULTIPLE_CHOICE and question.options:
            for i, option in enumerate(question.options):
                builder.button(text=f"{chr(65+i)}) {option}", callback_data=f"trivia_answer_{i}")
        await bot.send_message(session.user_id, text, reply_markup=builder.as_markup())

    @staticmethod
    async def send_answer_result(bot: Bot, session: TriviaSession, is_correct: bool, explanation: str):
        text = "\u2705 Correcto" if is_correct else "\u274C Incorrecto"
        if explanation:
            text += f"\n{explanation}"
        builder = InlineKeyboardBuilder()
        if session.current_question_index + 1 < len(session.questions):
            builder.button(text="Siguiente", callback_data="trivia_next")
        else:
            builder.button(text="Finalizar", callback_data="trivia_complete")
        await bot.send_message(session.user_id, text, reply_markup=builder.as_markup())
