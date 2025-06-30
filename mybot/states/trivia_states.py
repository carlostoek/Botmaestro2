from aiogram.fsm.state import StatesGroup, State

class TriviaStates(StatesGroup):
    waiting_trigger = State()
    trivia_intro = State()
    answering_question = State()
    waiting_answer = State()
    processing_answer = State()
    showing_result = State()
    showing_explanation = State()
    session_complete = State()
    reward_processing = State()
    unlocking_content = State()
