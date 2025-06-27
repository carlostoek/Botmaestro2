from aiogram.fsm.state import StatesGroup, State

class LorePieceAdminStates(StatesGroup):
    creating_code_name = State()
    creating_title = State()
    creating_description = State()
    creating_category = State()
    confirming_main_story = State()
    choosing_content_type = State()
    entering_text_content = State()
    uploading_file_content = State()
