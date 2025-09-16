from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Меню"), KeyboardButton(text="Собрать шаурму")],
        [KeyboardButton(text="Статус заказа"), KeyboardButton(text="Акции")],
        [KeyboardButton(text="Рандомный набор"), KeyboardButton(text="Помощь")],
        [KeyboardButton(text="💰 Применить промокод"), KeyboardButton(text="💎 Мои бонусы")]
    ],
    resize_keyboard=True
)

size_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Маленькая"), KeyboardButton(text="Средняя")],
        [KeyboardButton(text="Большая"), KeyboardButton(text="Королевская")]
    ],
    resize_keyboard=True
)

bonus_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💳 Использовать бонусы")],
        [KeyboardButton(text="⬅️ Назад в меню")]
    ],
    resize_keyboard=True
)