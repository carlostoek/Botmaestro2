from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_decision_keyboard(fragment):
    builder = InlineKeyboardBuilder()
    
    # Agregar botones para cada decisión disponible
    for index, decision in enumerate(fragment.decisions):
        builder.button(
            text=decision["text"],
            callback_data=f"narrative_choice:{fragment.fragment_id}:{index}"
        )
    
    # Botón para ver el estado de la historia
    builder.button(
        text="📖 Estado de mi historia",
        callback_data="story_status"
    )
    
    builder.adjust(1)  # Un botón por fila
    return builder.as_markup()
