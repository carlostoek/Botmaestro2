from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..database.narrative_models import NarrativeFragment, NarrativeDecision

def create_narrative_keyboard(fragment) -> InlineKeyboardMarkup:
    """
    Dynamically creates the InlineKeyboardMarkup with decision buttons for a fragment.
    """
    buttons = []
    for decision in fragment.decisions:
        # Here we would also check conditions before adding the button
        button = InlineKeyboardButton(
            text=decision.text,
            callback_data=f"narrative:decision:{decision.id}"
        )
        buttons.append([button])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard