from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


def get_trivia_options_keyboard(question_id: int, options: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for idx, option in enumerate(options):
        builder.button(text=option, callback_data=f"trivia_answer:{question_id}:{idx}")
    builder.adjust(1)
    return builder.as_markup()


def get_trivia_retry_keyboard(question_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Intentar de nuevo", callback_data=f"trivia_retry:{question_id}")
    builder.button(text="❌ Cancelar", callback_data="trivia_cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_generic_back_keyboard(callback: str = "trivia_back") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Volver", callback_data=callback)
    builder.adjust(1)
    return builder.as_markup()


def get_trivia_options_keyboard(options: List[str], question_id: int) -> InlineKeyboardMarkup:
    """
    Genera un teclado inline con las opciones de una trivia.
    Cada botón lleva el ID de la pregunta y la opción seleccionada como callback_data.
    """
    buttons = []
    for option_text in options:
        callback_data = f"trivia_answer:{question_id}:{option_text}"
        buttons.append([InlineKeyboardButton(text=option_text, callback_data=callback_data)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_trivia_retry_keyboard(question_id: int) -> InlineKeyboardMarkup:
    """
    Genera un teclado inline para ofrecer un reintento de la misma trivia.
    """
    buttons = [
        [InlineKeyboardButton(text="🔄 Reintentar Trivia", callback_data=f"trivia_retry:{question_id}")],
        [InlineKeyboardButton(text="🚫 Dejar así", callback_data=f"trivia_cancel_retry:{question_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_generic_back_keyboard(callback_data: str = "back_to_main_menu") -> InlineKeyboardMarkup:
    """
    Genera un teclado simple con un botón de 'Volver' o 'Menú Principal'.
    Útil para después de una trivia o en caso de error.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Volver al Menú Principal", callback_data=callback_data)]
    ])
