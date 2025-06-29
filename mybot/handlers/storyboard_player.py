from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.storyboard_service import StoryboardService

router = Router()

user_story_progress = {}

@router.message(Command("play_story"))
async def start_story(message: Message):
    scene_id = "intro"  # Escena inicial por defecto
    user_story_progress[message.from_user.id] = {"scene_id": scene_id, "order": 1}
    await send_next_dialogue(message.chat.id, message.from_user.id)

async def send_next_dialogue(chat_id, user_id):
    progress = user_story_progress.get(user_id)
    if not progress:
        return

    scene_id = progress["scene_id"]
    order = progress["order"]

    dialogues = await StoryboardService.get_scene_dialogues(scene_id)

    # Validación 1: Si no hay diálogos
    if not dialogues:
        await router.bot.send_message(chat_id, "Esta escena no tiene diálogos disponibles.")
        return

    # Validación 2: Si se pasaron del límite
    if order > len(dialogues):
        await router.bot.send_message(chat_id, "Has llegado al final de la escena.")
        return

    dialogue = dialogues[order - 1]
    text = f"*{dialogue.character}*\n{dialogue.dialogue}"

    # Validación 3: Si el texto está vacío
    if not dialogue.dialogue.strip():
        await router.bot.send_message(chat_id, "Este diálogo está vacío. Contacta al administrador.")
        return

    if dialogue.media_type == 'text':
        keyboard = InlineKeyboardBuilder().button(text="Siguiente", callback_data="next_dialogue").as_markup()
        await router.bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)

    progress["order"] += 1

@router.callback_query(F.data == "next_dialogue")
async def handle_next_dialogue(callback: CallbackQuery):
    await send_next_dialogue(callback.message.chat.id, callback.from_user.id)
