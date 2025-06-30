from aiogram.fsm.state import State, StatesGroup

class TriviaAdminStates(StatesGroup):
    # Estados para gestión de preguntas
    waiting_question_text = State()
    waiting_question_type = State()
    waiting_question_options = State()
    waiting_correct_answer = State()
    waiting_explanation = State()
    waiting_difficulty = State()
    waiting_time_limit = State()
    waiting_media_upload = State()

    # Estados para gestión de templates
    waiting_template_name = State()
    waiting_template_description = State()
    waiting_trigger_events = State()
    waiting_trigger_conditions = State()
    waiting_reward_config = State()
    waiting_question_selection = State()

    # Estados para edición
    editing_question = State()
    editing_template = State()

    # Estados para vista previa
    preview_question = State()
    preview_template = State()
