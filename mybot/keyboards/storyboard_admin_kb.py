from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_storyboard_admin_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='➕ Crear Nueva Escena', callback_data='create_scene')],
        [InlineKeyboardButton(text='➕ Agregar Diálogo', callback_data='add_dialogue')],
        [InlineKeyboardButton(text='✏️ Editar Diálogo', callback_data='edit_dialogue')],
        [InlineKeyboardButton(text='❌ Eliminar Diálogo', callback_data='delete_dialogue')],
        [InlineKeyboardButton(text='📜 Listar Escenas', callback_data='list_scenes')]
    ])
    return keyboard
