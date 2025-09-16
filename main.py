import asyncio
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from config import bot_token

# Импортируем обработчики из handlers.py
from handlers import (
    start_command, help_command, show_menu, start_order, process_size,
    process_ingredients, process_payment_callback, check_payment_callback,
    order_status, start_promo, apply_promo, random_combo, promotions, unknown_command,
    handle_alternative_payment, show_bonuses, use_bonuses_command, bonus_button_handler,
    use_bonuses_button, back_to_menu, process_bonus_amount, order_status_button
)

from states import OrderState, PromoState
from keyboards import main_keyboard

# Удаляем вебхук
url = f'https://api.telegram.org/bot{bot_token}/deleteWebhook'
response = requests.get(url)
print(response.json())

bot = Bot(token=bot_token)
dp = Dispatcher()

# Регистрируем обработчики
dp.message.register(start_command, Command("start"))
dp.message.register(help_command, Command("help"))
dp.message.register(help_command, F.text == "Помощь")
dp.message.register(show_menu, Command("menu"))
dp.message.register(show_menu, F.text == "Меню")
dp.message.register(start_order, Command("order"))
dp.message.register(start_order, F.text == "Собрать шаурму")
dp.message.register(process_size, OrderState.choosing_size)
dp.message.register(process_ingredients, OrderState.choosing_ingredients)
dp.message.register(order_status, Command("status"))
dp.message.register(order_status_button, F.text == "Статус заказа")  # Отдельный обработчик для кнопки
dp.message.register(start_promo, Command("promo"))
dp.message.register(start_promo, F.text == "💰 Применить промокод")
dp.message.register(apply_promo, PromoState.waiting_for_promo)
dp.message.register(random_combo, Command("random"))
dp.message.register(random_combo, F.text == "Рандомный набор")
dp.message.register(promotions, Command("promotions"))
dp.message.register(promotions, F.text == "Акции")
dp.message.register(show_bonuses, Command("bonus"))
dp.message.register(bonus_button_handler, F.text == "💎 Мои бонусы")
dp.message.register(use_bonuses_command, Command("use_bonus"))
dp.message.register(use_bonuses_button, F.text == "💳 Использовать бонусы")
dp.message.register(back_to_menu, F.text == "⬅️ Назад в меню")

# ОБЯЗАТЕЛЬНО: обработчик состояния для бонусов ДО unknown_command
dp.message.register(process_bonus_amount, PromoState.waiting_for_bonus_amount)

# Обработчики callback запросов
dp.callback_query.register(process_payment_callback, F.data.startswith("pay_"))
dp.callback_query.register(check_payment_callback, F.data.startswith("check_payment_"))
dp.callback_query.register(handle_alternative_payment, F.data.startswith("alt_paid_"))

# Неизвестные команды (должен быть ПОСЛЕДНИМ)
dp.message.register(unknown_command)

# Основная функция при запуске бота
async def main():
    print("Бот ROYALSHAWA запущен!")
    print("Доступные команды:")
    print("• /start - Приветствие")
    print("• /help - Справка по командам")
    print("• /menu - Показать меню")
    print("• /order - Начать заказ")
    print("• /status - Статус заказа")
    print("• /promo - Применить промокод")
    print("• /random - Случайный набор")
    print("• /promotions - Акции и скидки")
    print("• /bonus - Информация о бонусах")
    print("• /use_bonus - Использовать бонусы")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())