from aiogram.fsm.state import State, StatesGroup

class OrderState(StatesGroup):
    choosing_size = State()
    choosing_ingredients = State()
    special_requests = State()
    payment = State()

class PromoState(StatesGroup):
    waiting_for_promo = State()
    waiting_for_bonus_amount = State()