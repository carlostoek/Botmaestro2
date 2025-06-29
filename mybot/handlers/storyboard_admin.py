from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from keyboards.storyboard_admin_kb import get_storyboard_admin_kb
from services.storyboard_service import StoryboardService
from utils.admin_state import StoryboardStates

router = Router()


@router.message(Command("storyboard_admin"))
async def show_storyboard_menu(message: Message):
    await message.answer("🗂️ Storyboard Admin", reply_markup=get_storyboard_admin_kb())


@router.callback_query(F.data == "create_scene")
async def handle_create_scene(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Escribe el ID de la nueva escena:")
    await state.set_state(StoryboardStates.waiting_scene_id)


@router.message(F.text, state=StoryboardStates.waiting_scene_id)
async def receive_scene_id(message: Message, state: FSMContext):
    scene_id = message.text
    await StoryboardService.create_scene(scene_id)
    await message.answer(f"✅ Escena '{scene_id}' creada.")
    await state.clear()


@router.callback_query(F.data == "list_scenes")
async def handle_list_scenes(callback: CallbackQuery):
    scenes = await StoryboardService.get_all_scenes()
    text = "\n".join([f"- {scene}" for scene in scenes]) or "No hay escenas."
    await callback.message.answer(f"📚 Escenas disponibles:\n{text}")


# Agregar diálogo
@router.callback_query(F.data == "add_dialogue")
async def start_add_dialogue(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🔢 Ingresa el ID de la escena donde quieres agregar el diálogo:")
    await state.set_state(StoryboardStates.waiting_dialogue_scene)


@router.message(F.text, state=StoryboardStates.waiting_dialogue_scene)
async def receive_scene_for_dialogue(message: Message, state: FSMContext):
    await state.update_data(scene_id=message.text)
    await message.answer("🔢 Ingresa el orden del diálogo (número):")
    await state.set_state(StoryboardStates.waiting_dialogue_order)


@router.message(F.text, state=StoryboardStates.waiting_dialogue_order)
async def receive_order_for_dialogue(message: Message, state: FSMContext):
    await state.update_data(order=int(message.text))
    await message.answer("👤 Ingresa el nombre del personaje que habla:")
    await state.set_state(StoryboardStates.waiting_dialogue_character)


@router.message(F.text, state=StoryboardStates.waiting_dialogue_character)
async def receive_character_for_dialogue(message: Message, state: FSMContext):
    await state.update_data(character=message.text)
    await message.answer("💬 Ingresa el texto del diálogo:")
    await state.set_state(StoryboardStates.waiting_dialogue_text)


@router.message(F.text, state=StoryboardStates.waiting_dialogue_text)
async def receive_text_for_dialogue(message: Message, state: FSMContext):
    await state.update_data(dialogue=message.text)
    await message.answer("📂 Tipo de contenido (text, photo, audio):")
    await state.set_state(StoryboardStates.waiting_dialogue_media_type)


@router.message(F.text, state=StoryboardStates.waiting_dialogue_media_type)
async def receive_media_type_for_dialogue(message: Message, state: FSMContext):
    await state.update_data(media_type=message.text)
    await message.answer("📎 Ruta del archivo multimedia (opcional, escribe 'none' si no aplica):")
    await state.set_state(StoryboardStates.waiting_dialogue_media_path)


@router.message(F.text, state=StoryboardStates.waiting_dialogue_media_path)
async def receive_media_path_for_dialogue(message: Message, state: FSMContext):
    media_path = message.text if message.text.lower() != 'none' else None
    await state.update_data(media_path=media_path)
    await message.answer("🔐 Condición opcional (escribe 'none' si no aplica):")
    await state.set_state(StoryboardStates.waiting_dialogue_condition)


@router.message(F.text, state=StoryboardStates.waiting_dialogue_condition)
async def receive_condition_for_dialogue(message: Message, state: FSMContext):
    condition = message.text if message.text.lower() != 'none' else None
    data = await state.get_data()

    await StoryboardService.add_dialogue(
        scene_id=data['scene_id'],
        order=data['order'],
        character=data['character'],
        dialogue=data['dialogue'],
        media_type=data['media_type'],
        media_path=data['media_path'],
        condition=condition
    )

    await message.answer("✅ Diálogo agregado exitosamente.")
    await state.clear()


# Editar diálogo
@router.callback_query(F.data == "edit_dialogue")
async def start_edit_dialogue(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Ingresa el ID del diálogo que quieres editar:")
    await state.set_state(StoryboardStates.waiting_dialogue_id_edit)


@router.message(F.text, state=StoryboardStates.waiting_dialogue_id_edit)
async def receive_dialogue_id_for_edit(message: Message, state: FSMContext):
    dialogue_id = int(message.text)
    await state.update_data(dialogue_id=dialogue_id)
    await message.answer("✏️ Ingresa el nuevo texto del diálogo:")
    await state.set_state(StoryboardStates.waiting_dialogue_text)


@router.message(F.text, state=StoryboardStates.waiting_dialogue_text)
async def edit_dialogue_text(message: Message, state: FSMContext):
    data = await state.get_data()
    await StoryboardService.edit_dialogue(data['dialogue_id'], dialogue=message.text)
    await message.answer("✅ Diálogo actualizado exitosamente.")
    await state.clear()


# Eliminar diálogo
@router.callback_query(F.data == "delete_dialogue")
async def start_delete_dialogue(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("❌ Ingresa el ID del diálogo que quieres eliminar:")
    await state.set_state(StoryboardStates.waiting_dialogue_id_delete)


@router.message(F.text, state=StoryboardStates.waiting_dialogue_id_delete)
async def receive_dialogue_id_for_delete(message: Message, state: FSMContext):
    dialogue_id = int(message.text)
    await StoryboardService.delete_dialogue(dialogue_id)
    await message.answer("✅ Diálogo eliminado exitosamente.")
    await state.clear()
