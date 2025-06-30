from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_trivia_main_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="❓ Preguntas", callback_data="admin_trivia_questions")
    builder.button(text="📂 Templates", callback_data="admin_trivia_templates")
    builder.button(text="📊 Analytics", callback_data="admin_trivia_analytics")
    builder.button(text="⚙️ Configuración", callback_data="admin_trivia_config")
    builder.button(text="🔴 Trivias Activas", callback_data="admin_trivia_sessions")
    builder.button(text="🔙 Volver", callback_data="admin_main_menu")
    builder.adjust(1)
    return builder.as_markup()
