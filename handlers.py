from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram import F
from aiogram.fsm.context import FSMContext
import random
from datetime import datetime, timedelta
from states import OrderState, PromoState
from keyboards import main_keyboard, size_keyboard, bonus_keyboard
from database import user_orders, user_promos, promo_codes, user_bonuses, loyalty_levels
from payment import create_payment, check_payment_status
from utils import check_order_status, calculate_level, add_bonuses


async def start_command(message: Message):
    welcome_text = (
        f" **Приветствую вас, {message.from_user.first_name}!** \n\n"
        "Добро пожаловать на королевскую кухню для эксклюзивных клиентов\n"
        "Я — ваш личный помощник по заказу королевской шаурмы!\n\n"
        "**Я помогу тебе:**\n"
        "• Составить особый рецепт шаурмы, отвечающий твоим королевским вкусам \n"
        "• Посмотреть обширное меню с ценами и описанием\n"
        "• Узнать о текущих акциях и промокодах\n"
        "• Проверить статус заказа\n"
        "• Создать случайный вкусный набор\n"
        "• Накопить бонусы и повысить уровень лояльности\n\n"
        "Используйте кнопки ниже или команды для навигации!"
    )

    await message.answer(welcome_text, reply_markup=main_keyboard)

    # Инициализация пользователя в системе
    user_id = message.from_user.id
    user_orders[user_id] = {
        'orders': [],
        'first_interaction': datetime.now(),
        'total_spent': 0
    }

    user_promos[user_id] = {
        'applied_promos': [],
        'active_discount': 0
    }

    # Инициализация бонусной системы
    if user_id not in user_bonuses:
        user_bonuses[user_id] = {
            'bonus_points': 0,
            'total_spent': 0,
            'loyalty_level': 'bronze',
            'cashback_earned': 0
        }


async def help_command(message: Message):
    help_text = (
        "**Доступные команды:**\n\n"
        "**Основные команды:**\n"
        "/start - Начало работы с ботом\n"
        "/help - Получить справку по командам\n"
        "/menu - Показать меню с ценами\n"
        "/order - Начать процесс заказа\n"
        "/status [номер] - Проверить статус заказа\n"
        "/promo [код] - Применить промокод\n"
        "/random - Случайный набор шаурмы\n"
        "/bonus - Информация о бонусах\n"
        "/use_bonus - Использовать бонусы\n\n"
        "**Дополнительные функции:**\n"
        "• Подбор ингредиентов по предпочтениям\n"
        "• Расчет стоимости с учетом скидок\n"
        "• Генерация уникальных рецептов\n"
        "• Оплата заказов через ЮKassa\n"
        "• Накопительная система бонусов\n"
        "• Уровни лояльности (бронза, серебро, золото, платина)"
    )
    await message.answer(help_text)


async def show_menu(message: Message):
    # Парсинг аргументов команды
    command_parts = message.text.split()
    category = command_parts[1].lower() if len(command_parts) > 1 else "all"

    menu_items = {
        "classic": [
            "**Классическая шаурма** - 200₽\nСостав: курица, овощи, соус кетчуп-майонез",
            "**Острая шаурма** - 220₽\nСостав: курица, овощи, острый соус чили"
        ],
        "premium": [
            "**Королевская шаурма** - 500₽\nСостав: говядина, курица, свинина, овощи, секретный фирменный соус",
            "**Морская шаурма** - 390₽\nСостав: креветки, овощи, чесночный соус"
        ],
        "veg": [
            "**Вегетарианская** - 150₽\nСостав: овощи на гриле, брусничный соус",
            "**Веганская** - 190₽\nСостав: тофу, овощи, брусничный соус"
        ]
    }

    if category == "all":
        response = "**Полное меню ROYAL$HAWA** \n\n"
        for category_name, items in menu_items.items():
            response += f"**{category_name.upper()}:**\n" + "\n".join(items) + "\n\n"
    elif category in menu_items:
        response = f"**Меню: {category.upper()}** \n\n" + "\n".join(menu_items[category])
    else:
        response = "Категория не найдена. Доступные категории: classic, premium, veg"

    response += "\n\nИспользуйте /menu [категория] для фильтрации"
    await message.answer(response)


async def start_order(message: Message, state: FSMContext):
    await message.answer(
        "**Соберите свою королевскую шаурму!**\n\n"
        "Выберите размер порции:",
        reply_markup=size_keyboard
    )
    await state.set_state(OrderState.choosing_size)


async def process_size(message: Message, state: FSMContext):
    sizes = {"Маленькая": 50, "Средняя": 70, "Большая": 80, "Королевская": 100}

    if message.text not in sizes:
        await message.answer("Пожалуйста, выберите размер из предложенных вариантов")
        return

    await state.update_data(size=message.text, base_price=sizes[message.text])

    ingredients_text = (
        "**Выберите ингредиенты (через запятую):**\n\n"
        "**Мясо:** курица, говядина, свинина, креветки\n"
        "**Овощи:** салат, помидор, огурец, корейская морковка, красный лук, перец\n"
        "**Соусы:** классический(майонез-кетчуп), острый чили, чесночный, сырный, брусничный, кисло-сладкий\n\n"
        "Пример: курица, салат, помидор, классический(майонез-кетчуп)"
    )

    await message.answer(ingredients_text, reply_markup=None)
    await state.set_state(OrderState.choosing_ingredients)


async def process_ingredients(message: Message, state: FSMContext):
    """
    Обрабатывает выбор ингредиентов и рассчитывает итоговую стоимость
    """
    data = await state.get_data()
    base_price = data['base_price']

    # Анализируем выбранные ингредиенты
    ingredients = [ing.strip().lower() for ing in message.text.split(',')]

    # Логика расчета цены на основе ингредиентов
    price_modifiers = {
        'говядина': 140, 'креветки': 280, 'свинина': 120,
        'курица': 105, 'салат': 23, 'помидор': 15,
        'огурец': 10, 'корейская морковка': 7, 'красный лук': 6,
        'перец': 4, 'классический(майонез-кетчуп)': 30, 'острый чили': 40,
        'брусничный': 50, 'кисло-сладкий': 50, 'сырный': 30,
        'чесночный': 30, 'тофу': 60, 'маринованные овощи': 15,
    }

    final_price = base_price
    selected_ingredients = []

    for ing in ingredients:
        if ing in price_modifiers:
            final_price += price_modifiers[ing]
        selected_ingredients.append(ing)

    # ПРИМЕНЯЕМ СКИДКУ ЕСЛИ ЕСТЬ АКТИВНЫЙ ПРОМОКОД
    user_id = message.from_user.id
    discount_applied = False
    discount_amount = 0

    if user_id in user_promos and user_promos[user_id]['active_discount'] > 0:
        discount = user_promos[user_id]['active_discount']
        discount_amount = final_price * discount // 100
        final_price -= discount_amount
        discount_applied = True

    # ПРИМЕНЯЕМ БОНУСЫ ЕСЛИ ОНИ ЕСТЬ
    bonus_applied = False
    bonus_amount = 0
    if user_id in user_bonuses and user_bonuses[user_id].get('bonus_used', 0) > 0:
        bonus_to_use = user_bonuses[user_id]['bonus_used']
        # Максимум можно оплатить 50% стоимости заказа бонусами
        max_bonus_payment = final_price * 50 // 100
        bonus_amount = min(bonus_to_use, max_bonus_payment)
        final_price -= bonus_amount
        bonus_applied = True

    # Генерация номера заказа
    order_number = random.randint(1000, 9999)
    order_time = datetime.now() + timedelta(minutes=10)

    # ИНИЦИАЛИЗАЦИЯ ПОЛЬЗОВАТЕЛЯ В БОНУСНОЙ СИСТЕМЕ ЕСЛИ ЕГО ЕЩЕ НЕТ
    if user_id not in user_bonuses:
        user_bonuses[user_id] = {
            'bonus_points': 0,
            'total_spent': 0,
            'loyalty_level': 'bronze',
            'cashback_earned': 0
        }

    # Получаем информацию о бонусах пользователя
    user_level = user_bonuses[user_id]['loyalty_level']
    cashback_percent = loyalty_levels[user_level]['cashback']
    bonus_earned = final_price * cashback_percent // 100

    # Сохраняем данные заказа в состоянии
    await state.update_data(
        order_number=order_number,
        selected_ingredients=selected_ingredients,
        final_price=final_price,
        discount_applied=discount_applied,
        discount_amount=discount_amount,
        bonus_applied=bonus_applied,
        bonus_amount=bonus_amount,
        order_time=order_time
    )

    response = (
        f"**Ваш заказ #{order_number}:**\n\n"
        f"**Состав:** {', '.join(selected_ingredients)}\n"
        f"**Итоговая стоимость:** {final_price}₽\n"
    )

    # Добавляем информацию о скидке если она была применена
    if discount_applied:
        response += f"**Скидка:** {user_promos[user_id]['active_discount']}% (-{discount_amount}₽)\n"

    # Добавляем информацию о бонусах если они были применены
    if bonus_applied:
        response += f"**Оплачено бонусами:** -{bonus_amount}₽\n"

    response += (
        f"**Бонусов к начислению:** {bonus_earned} ({cashback_percent}%)\n"
        f"**Примерное время готовности:** {order_time.strftime('%H:%M')}\n\n"
        "Для оплаты заказа нажмите кнопку ниже 👇"
    )

    # Создаем кнопку для оплаты
    payment_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить заказ", callback_data=f"pay_{order_number}")]
        ]
    )

    await message.answer(response, reply_markup=payment_keyboard)
    await state.set_state(OrderState.payment)


async def order_status(message: Message):
    """
    Проверяет статус заказа пользователя
    """
    user_id = message.from_user.id

    if user_id not in user_orders or not user_orders[user_id]['orders']:
        await message.answer("❌ У вас нет активных заказов")
        return

    # Проверяем, это команда с аргументом или просто кнопка
    if message.text.startswith('/status'):
        # Парсим номер заказа из команды, если указан
        command_parts = message.text.split()
        if len(command_parts) > 1:
            try:
                order_number = int(command_parts[1])
                # Ищем конкретный заказ
                for order in user_orders[user_id]['orders']:
                    if order['number'] == order_number:
                        order = check_order_status(order)
                        status_text = (
                            f"📦 **Статус заказа #{order['number']}**\n\n"
                            f"**Состав:** {', '.join(order['items'])}\n"
                            f"**Стоимость:** {order['final_price']}₽\n"
                            f"**Статус:** {order['status']}\n"
                        )

                        if 'estimated_time' in order:
                            status_text += f"**Время готовности:** {order['estimated_time'].strftime('%H:%M')}\n"

                        if order.get('discount_applied'):
                            status_text += f"**Скидка:** {order['discount_amount']}₽\n"

                        if order.get('bonus_applied'):
                            status_text += f"**Оплачено бонусами:** {order['bonus_amount']}₽\n"

                        await message.answer(status_text)
                        return

                await message.answer(f"❌ Заказ #{order_number} не найден")

            except ValueError:
                await message.answer("❌ Неверный формат номера заказа. Используйте: /status [номер]")
            return

    # Если это просто кнопка "Статус заказа" без номера - показываем все заказы
    response = "📦 **Ваши заказы:**\n\n"
    for order in user_orders[user_id]['orders']:
        order = check_order_status(order)
        order_status_emoji = "✅" if "Готов" in order['status'] else "⏳" if "обработк" in order['status'] else "📦"

        response += (
            f"{order_status_emoji} **Заказ #{order['number']}** - {order['status']}\n"
            f"💵 Стоимость: {order['final_price']}₽\n"
        )

        if 'estimated_time' in order:
            from utils import format_time_remaining
            time_remaining = format_time_remaining(order['estimated_time'])
            response += f"⏰ Осталось: {time_remaining}\n"

        response += "\n"

    response += "Для детальной информации используйте: /status [номер_заказа]\n"
    response += "Например: /status 1234"
    await message.answer(response)


async def order_status_button(message: Message):
    """
    Обработчик для кнопки "Статус заказа"
    """
    user_id = message.from_user.id

    if user_id not in user_orders or not user_orders[user_id]['orders']:
        await message.answer("❌ У вас нет активных заказов")
        return

    # Показываем все заказы
    response = "📦 **Ваши заказы:**\n\n"
    for order in user_orders[user_id]['orders']:
        order = check_order_status(order)
        order_status_emoji = "✅" if "Готов" in order['status'] else "⏳" if "обработк" in order['status'] else "📦"

        response += (
            f"{order_status_emoji} **Заказ #{order['number']}** - {order['status']}\n"
            f"💵 Стоимость: {order['final_price']}₽\n"
        )

        if 'estimated_time' in order:
            time_remaining = format_time_remaining(order['estimated_time'])
            response += f"⏰ Готов через: {time_remaining}\n"

        response += "\n"

    response += "Для детальной информации используйте: /status [номер_заказа]\n"
    response += "Например: /status 1234"
    await message.answer(response)


async def show_bonuses(message: Message):
    """
    Показывает информацию о бонусах пользователя
    """
    user_id = message.from_user.id

    if user_id not in user_bonuses:
        user_bonuses[user_id] = {
            'bonus_points': 0,
            'total_spent': 0,
            'loyalty_level': 'bronze',
            'cashback_earned': 0
        }

    bonus_info = user_bonuses[user_id]
    level_info = loyalty_levels[bonus_info['loyalty_level']]

    # Рассчитываем до следующего уровня
    next_level = None
    next_level_name = None
    levels = list(loyalty_levels.keys())
    current_index = levels.index(bonus_info['loyalty_level'])

    if current_index < len(levels) - 1:
        next_level_name = levels[current_index + 1]
        next_level = loyalty_levels[next_level_name]
        to_next_level = next_level['min_spent'] - bonus_info['total_spent']

    bonus_text = (
        f"💎 **Ваши бонусы**\n\n"
        f"**Баланс бонусов:** {bonus_info['bonus_points']}₽\n"
        f"**Уровень лояльности:** {bonus_info['loyalty_level'].upper()}\n"
        f"**Кэшбек:** {level_info['cashback']}%\n"
        f"**Минимальная скидка:** {level_info['min_discount']}%\n"
        f"**Всего потрачено:** {bonus_info['total_spent']}₽\n"
        f"**Всего заработано бонусов:** {bonus_info['cashback_earned']}₽\n\n"
    )

    if next_level:
        bonus_text += (
            f"**До уровня {next_level_name.upper()}:** {to_next_level}₽\n"
            f"Кэшбек: {next_level['cashback']}%\n"
            f"Минимальная скидка: {next_level['min_discount']}%\n\n"
        )

    bonus_text += (
        "**Как использовать бонусы:**\n"
        "• Максимум 50% стоимости заказа можно оплатить бонусами\n"
        "• Используйте команду /use_bonus [количество]\n"
        "• Или /use_bonus all - использовать все бонусы\n\n"
        "Бонусы автоматически начисляются после оплаты заказа!"
    )

    await message.answer(bonus_text, reply_markup=bonus_keyboard)

async def use_bonuses_button(message: Message, state: FSMContext):
    """
    Обработчик кнопки "Использовать бонусы"
    """
    user_id = message.from_user.id

    if user_id not in user_bonuses or user_bonuses[user_id]['bonus_points'] == 0:
        await message.answer(
            "❌ У вас нет доступных бонусов для использования\n\n"
            "Бонусы начисляются после оплаты заказов и могут быть использованы "
            "для оплаты до 50% стоимости следующего заказа.",
            reply_markup=main_keyboard
        )
        return

    await message.answer(
        "💰 **Использование бонусов**\n\n"
        f"Доступно бонусов: {user_bonuses[user_id]['bonus_points']}₽\n\n"
        "Введите количество бонусов, которые хотите использовать:\n"
        "• Можно ввести конкретную сумму (например: 100)\n"
        "• Или 'all' чтобы использовать все доступные бонусы\n\n"
        "💡 **Важно:** Максимум можно оплатить 50% стоимости заказа бонусами",
        reply_markup=bonus_keyboard
    )
    await state.set_state(PromoState.waiting_for_bonus_amount)


async def process_bonus_amount(message: Message, state: FSMContext):
    """
    Обрабатывает ввод количества бонусов для использования
    """
    user_id = message.from_user.id
    bonus_input = message.text.lower().strip()

    try:
        if bonus_input == 'all':
            bonus_to_use = user_bonuses[user_id]['bonus_points']
        else:
            bonus_to_use = int(bonus_input)

        if bonus_to_use <= 0:
            await message.answer("❌ Введите положительное число бонусов")
            return

        if bonus_to_use > user_bonuses[user_id]['bonus_points']:
            await message.answer("❌ Недостаточно бонусов")
            return

        # Сохраняем информацию об использовании бонусов
        user_bonuses[user_id]['bonus_used'] = bonus_to_use

        await message.answer(
            f"✅ Готово! {bonus_to_use}₽ бонусов будет списано с вашего счета при следующем заказе\n\n"
            f"Остаток бонусов: {user_bonuses[user_id]['bonus_points'] - bonus_to_use}₽\n\n"
            "Теперь перейдите к созданию заказа с помощью кнопки '🍔 Собрать шаурму'",
            reply_markup=main_keyboard
        )
        await state.clear()

    except ValueError:
        await message.answer(
            "❌ Неверный формат. Введите число или 'all'\n\n"
            "Примеры:\n"
            "• 100 - использовать 100 бонусов\n"
            "• all - использовать все бонусы"
        )


async def back_to_menu(message: Message, state: FSMContext):
    """
    Обработчик кнопки "Назад в меню"
    """
    await state.clear()
    await message.answer(
        "⬅️ Возвращаемся в главное меню\n\n"
        "Выберите действие:",
        reply_markup=main_keyboard
    )


async def start_promo(message: Message, state: FSMContext):
    """
    Начинает процесс применения промокода
    """
    await message.answer(
        "🎁 **Применение промокода**\n\n"
        "Введите промокод для получения скидки:\n\n"
        "Доступные промокоды:\n"
        "• STUDENT - 10% скидка\n"
        "• KING - 20% скидка\n"
        "• HPB - 30% скидка"
    )
    await state.set_state(PromoState.waiting_for_promo)


async def apply_promo(message: Message, state: FSMContext):
    """
    Применяет промокод к аккаунту пользователя
    """
    user_id = message.from_user.id
    promo_code = message.text.upper().strip()

    if promo_code in promo_codes:
        discount = promo_codes[promo_code]

        # Инициализируем систему промокодов для пользователя
        if user_id not in user_promos:
            user_promos[user_id] = {
                'applied_promos': [],
                'active_discount': 0
            }

        # Проверяем, не применялся ли уже этот промокод
        if promo_code in user_promos[user_id]['applied_promos']:
            await message.answer(f"❌ Промокод {promo_code} уже был применен ранее")
            await state.clear()
            return

        # Применяем промокод
        user_promos[user_id]['applied_promos'].append(promo_code)
        user_promos[user_id]['active_discount'] = discount

        await message.answer(
            f"✅ Промокод {promo_code} успешно применен!\n"
            f"Вы получили скидку {discount}% на следующий заказ\n\n"
            f"Теперь перейдите к созданию заказа с помощью кнопки 'Собрать шаурму'"
        )
        await state.clear()

    else:
        await message.answer(
            f"❌ Промокод {promo_code} не найден или недействителен\n\n"
            "Доступные промокоды:\n"
            "• STUDENT - 10% скидка\n"
            "• KING - 20% скидка\n"
            "• HPB - 30% скидка\n\n"
            "Попробуйте ввести другой промокод или проверьте правильность написания"
        )


async def random_combo(message: Message):
    """
    Создает случайный набор шаурмы
    """
    # Ингредиенты для случайного набора
    meats = ["курица", "говядина", "свинина", "креветки"]
    vegetables = ["салат", "помидор", "огурец", "корейская морковка", "красный лук", "перец"]
    sauces = ["классический(майонез-кетчуп)", "острый чили", "чесночный", "сырный", "брусничный", "кисло-сладкий"]

    # Выбираем случайные ингредиенты
    random_meat = random.choice(meats)
    random_veggies = random.sample(vegetables, random.randint(2, 4))
    random_sauce = random.choice(sauces)

    # Собираем все ингредиенты
    all_ingredients = [random_meat] + random_veggies + [random_sauce]

    # Рассчитываем стоимость
    price_modifiers = {
        'говядина': 140, 'креветки': 280, 'свинина': 120,
        'курица': 105, 'салат': 23, 'помидор': 15,
        'огурец': 10, 'корейская морковка': 7, 'красный лук': 6,
        'перец': 4, 'классический(майонез-кетчуп)': 30, 'острый чили': 40,
        'брусничный': 50, 'кисло-сладкий': 50, 'сырный': 30,
        'чесночный': 30, 'тофу': 60, 'маринованные овощи': 15,
    }

    base_price = 70  # Средний размер
    final_price = base_price

    for ing in all_ingredients:
        if ing in price_modifiers:
            final_price += price_modifiers[ing]

    response = (
        "🎲 **Случайный королевский набор!**\n\n"
        f"**Состав:** {', '.join(all_ingredients)}\n"
        f"**Примерная стоимость:** {final_price}₽\n\n"
        "Хотите заказать этот набор?\n"
        "Используйте кнопку 'Собрать шаурму' и введите эти ингредиенты!"
    )

    await message.answer(response)


async def promotions(message: Message):
    """
    Показывает текущие акции и промокоды
    """
    promo_text = (
        "🎁 **Акции и промокоды ROYAL$HAWA**\n\n"
        "**Постоянные промокоды:**\n"
        "• STUDENT - 10% скидка для студентов\n"
        "• KING - 20% скидка для королевских гостей\n"
        "• HPB - 30% скидка для самых верных поклонников\n\n"
        "**Текущие акции:**\n"
        "• Каждый 5-й заказ со скидкой 15%\n"
        "• Бесплатная доставка при заказе от 1000₽\n"
        "• Двойные бонусы по выходным\n\n"
        "**Накопительная система:**\n"
        "• Бронза (от 0₽) - 5% кэшбек\n"
        "• Серебро (от 2000₽) - 7% кэшбек + скидка 10%\n"
        "• Золото (от 5000₽) - 10% кэшбек + скидка 15%\n"
        "• Платина (от 10000₽) - 15% кэшбек + скидка 20%\n\n"
        "Используйте /promo [код] для применения промокода"
    )

    await message.answer(promo_text)


async def process_payment_callback(callback_query: CallbackQuery, state: FSMContext):
    order_number = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id

    # Получаем данные из состояния
    data = await state.get_data()

    if data.get('order_number') != order_number:
        await callback_query.answer("Ошибка: неверный номер заказа")
        return

    final_price = data['final_price']
    selected_ingredients = data['selected_ingredients']
    bonus_applied = data.get('bonus_applied', False)
    bonus_amount = data.get('bonus_amount', 0)

    # Рассчитываем бонусы
    user_level = user_bonuses[user_id]['loyalty_level']
    cashback_percent = loyalty_levels[user_level]['cashback']
    bonus_earned = final_price * cashback_percent // 100

    # Создаем платеж в ЮKassa
    try:
        payment_url, payment_id = await create_payment(
            final_price,
            f"Заказ шаурмы #{order_number}",
            user_id,
            order_number
        )

        # Сохраняем информацию о заказе
        if user_id not in user_orders:
            user_orders[user_id] = {'orders': [], 'total_spent': 0}

        user_orders[user_id]['orders'].append({
            'number': order_number,
            'items': selected_ingredients,
            'price': final_price + bonus_amount,  # Общая стоимость до применения бонусов
            'final_price': final_price,  # Стоимость после применения бонусов
            'status': 'Ожидает оплаты',
            'estimated_time': data['order_time'],
            'discount_applied': data['discount_applied'],
            'discount_amount': data['discount_amount'],
            'bonus_applied': bonus_applied,
            'bonus_amount': bonus_amount,
            'payment_id': payment_id,
            'bonus_earned': bonus_earned
        })

        # Отправляем пользователю ссылку для оплаты
        payment_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_url)],
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_payment_{payment_id}")]
            ]
        )

        payment_text = (
            f"**Заказ #{order_number} ожидает оплаты**\n\n"
            f"Сумма к оплате: {final_price}₽\n"
        )

        if bonus_applied:
            payment_text += f"Оплачено бонусами: {bonus_amount}₽\n"

        payment_text += f"Бонусов к начислению: {bonus_earned}\n\nНажмите на кнопку ниже для перехода к оплате:"

        await callback_query.message.edit_text(
            payment_text,
            reply_markup=payment_keyboard
        )

        await callback_query.answer()

    except Exception as e:
        print(f"Ошибка при создании платежа: {e}")

        # Сохраняем заказ даже при ошибке платежа
        if user_id not in user_orders:
            user_orders[user_id] = {'orders': [], 'total_spent': 0}

        user_orders[user_id]['orders'].append({
            'number': order_number,
            'items': selected_ingredients,
            'price': final_price + bonus_amount,
            'final_price': final_price,
            'status': 'Ожидает оплаты (альтернативная)',
            'estimated_time': data['order_time'],
            'discount_applied': data['discount_applied'],
            'discount_amount': data['discount_amount'],
            'bonus_applied': bonus_applied,
            'bonus_amount': bonus_amount,
            'payment_method': 'альтернативная',
            'bonus_earned': bonus_earned
        })

        # Создаем клавиатуру с кнопкой "Оплата прошла"
        alternative_payment_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Оплата прошла", callback_data=f"alt_paid_{order_number}")]
            ]
        )

        payment_text = (
            "❌ **Произошла ошибка при создании платежа**\n\n"
            "Упс... Кажется, Юkassa временно не работает, но вы можете произвести оплату "
            "по номеру +7(967)XXX-XX-XX на Сбербанк. Чек покажите шефу при получении заказа.\n\n"
            f"**Сумма к оплате:** {final_price}₽\n"
        )

        if bonus_applied:
            payment_text += f"**Оплачено бонусами:** {bonus_amount}₽\n"

        payment_text += (
            f"**Бонусов к начислению:** {bonus_earned}\n"
            f"**Номер заказа:** #{order_number}\n\n"
            "После оплаты нажмите кнопку ниже:"
        )

        await callback_query.message.edit_text(
            payment_text,
            reply_markup=alternative_payment_keyboard
        )
        await callback_query.answer()


async def check_payment_callback(callback_query: CallbackQuery):
    payment_id = callback_query.data.split("_")[2]
    user_id = callback_query.from_user.id

    try:
        payment_status = await check_payment_status(payment_id)

        if payment_status == 'succeeded':
            # Находим заказ и обновляем его статус
            order_updated = False
            order_number = None
            order_data = None
            if user_id in user_orders:
                for order in user_orders[user_id]['orders']:
                    if order.get('payment_id') == payment_id:
                        order['status'] = 'В обработке'
                        order_number = order['number']
                        order_data = order

                        # Списание использованных бонусов
                        if order.get('bonus_applied', False):
                            bonus_amount = order.get('bonus_amount', 0)
                            if user_id in user_bonuses:
                                user_bonuses[user_id]['bonus_points'] -= bonus_amount
                                # Убираем флаг использованных бонусов
                                user_bonuses[user_id]['bonus_used'] = 0

                        # Начисляем бонусы за заказ
                        await add_bonuses(user_id, order['final_price'], order['bonus_earned'])

                        order_updated = True
                        break

            if order_updated:
                # Получаем обновленные данные о бонусах
                bonus_info = user_bonuses[user_id]
                new_level = calculate_level(bonus_info['total_spent'])

                level_up_message = ""
                if new_level != bonus_info['loyalty_level']:
                    user_bonuses[user_id]['loyalty_level'] = new_level
                    level_up_message = f"\n🎉 Поздравляем! Вы достигли уровня {new_level.upper()}!"

                status_text = (
                    "✅ **Оплата прошла успешно!**\n\n"
                    f"Ваш заказ #{order_number} принят в обработку.\n"
                    f"Примерное время готовности: {order_data['estimated_time'].strftime('%H:%M')}\n"
                    f"Начислено бонусов: {order_data['bonus_earned']}\n"
                    f"Всего бонусов: {bonus_info['bonus_points']}{level_up_message}"
                )

                await callback_query.message.edit_text(
                    status_text
                )

                # Отправляем отдельное сообщение с основной клавиатурой
                await callback_query.message.answer(
                    "Что бы вы хотели сделать дальше?",
                    reply_markup=main_keyboard
                )

        elif payment_status == 'pending':
            await callback_query.answer("⏳ Платеж еще обрабатывается. Попробуйте проверить позже.")

        elif payment_status == 'canceled':
            await callback_query.message.edit_text(
                "❌ **Платеж отменен**\n\n"
                "Вы можете попробовать оплатить еще раз.",
                reply_markup=main_keyboard
            )

        else:
            await callback_query.answer("⏳ Платеж обрабатывается. Попробуйте позже.")

    except Exception as e:
        print(f"Ошибка при проверке платежа: {e}")
        await callback_query.answer("⚠️ Произошла ошибка при проверке платежа. Попробуйте позже.")
        await callback_query.message.answer(
            "Что бы вы хотели сделать дальше?",
            reply_markup=main_keyboard
        )


async def handle_alternative_payment(callback_query: CallbackQuery):
    """
    Обрабатывает подтверждение альтернативной оплаты
    """
    try:
        order_number = int(callback_query.data.split("_")[2])
        user_id = callback_query.from_user.id

        # Находим заказ и обновляем статус
        order_updated = False
        order_data = None
        if user_id in user_orders:
            for order in user_orders[user_id]['orders']:
                if order['number'] == order_number:
                    order['status'] = 'В обработке'
                    order['payment_method'] = 'альтернативная (подтверждена)'

                    # Списание использованных бонусов
                    if order.get('bonus_applied', False):
                        bonus_amount = order.get('bonus_amount', 0)
                        if user_id in user_bonuses:
                            user_bonuses[user_id]['bonus_points'] -= bonus_amount
                            # Убираем флаг использованных бонусов
                            user_bonuses[user_id]['bonus_used'] = 0

                    # Начисляем бонусы
                    await add_bonuses(user_id, order['final_price'], order['bonus_earned'])

                    order_updated = True
                    order_data = order
                    break

        if order_updated and order_data:
            # Получаем обновленные данные о бонусаз
            bonus_info = user_bonuses[user_id]
            new_level = calculate_level(bonus_info['total_spent'])

            level_up_message = ""
            if new_level != bonus_info['loyalty_level']:
                user_bonuses[user_id]['loyalty_level'] = new_level
                level_up_message = f"\n🎉 Поздравляем! Вы достигли уровня {new_level.upper()}!"

            # Показываем статус заказа с основной клавиатурой
            status_text = (
                f"✅ **Оплата подтверждена!**\n\n"
                f"**Заказ #{order_number} принят в обработку.**\n"
                f"**Статус:** В обработке\n"
                f"**Примерное время готовности:** {order_data['estimated_time'].strftime('%H:%M')}\n"
                f"**Начислено бонусов:** {order_data['bonus_earned']}\n"
                f"**Всего бонусов:** {bonus_info['bonus_points']}{level_up_message}\n\n"
                "Ожидайте уведомления о готовности.\n"
                "Не забудьте показать чек повару при получении!"
            )

            await callback_query.message.edit_text(
                status_text
            )

            # Отправляем отдельное сообщение с основной клавиатурой
            await callback_query.message.answer(
                "Что бы вы хотели сделать дальше?",
                reply_markup=main_keyboard
            )

        else:
            await callback_query.message.edit_text(
                "❌ Не удалось найти заказ. Обратитесь к шефу лично.",
                reply_markup=main_keyboard
            )

    except Exception as e:
        print(f"Ошибка при обработке альтернативной оплаты: {e}")
        await callback_query.answer("Произошла ошибка. Попробуйте позже.")
        await callback_query.message.answer(
            "Что бы вы хотели сделать дальше?",
            reply_markup=main_keyboard
        )


async def use_bonuses_command(message: Message):
    """
    Обработчик команды для использования бонусов
    """
    user_id = message.from_user.id

    if user_id not in user_bonuses or user_bonuses[user_id]['bonus_points'] == 0:
        await message.answer("❌ У вас нет доступных бонусов для использования")
        return

    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.answer(
                "💰 **Использование бонусов**\n\n"
                f"Доступно бонусов: {user_bonuses[user_id]['bonus_points']}\n\n"
                "Используйте: /use_bonus [количество]\n"
                "Или: /use_bonus all - использовать все доступные\n\n"
                "Максимум можно оплатить 50% стоимости заказа бонусами"
            )
            return

        bonus_amount = command_parts[1].lower()

        if bonus_amount == 'all':
            bonus_to_use = user_bonuses[user_id]['bonus_points']
        else:
            bonus_to_use = int(bonus_amount)

        if bonus_to_use <= 0:
            await message.answer("❌ Введите положительное число бонусов")
            return

        if bonus_to_use > user_bonuses[user_id]['bonus_points']:
            await message.answer("❌ Недостаточно бонусов")
            return

        # Сохраняем информацию об использовании бонусов
        user_bonuses[user_id]['bonus_used'] = bonus_to_use

        await message.answer(
            f"✅ Готово! {bonus_to_use} бонусов будет списано с вашего счета при следующем заказе\n\n"
            f"Остаток бонусов: {user_bonuses[user_id]['bonus_points'] - bonus_to_use}\n\n"
            "Теперь перейдите к созданию заказа с помощью кнопки 'Собрать шаурму'"
        )

    except ValueError:
        await message.answer("❌ Неверный формат. Используйте: /use_bonus [количество]")


# Добавляем обработчик для кнопки "Мои бонусы"
async def bonus_button_handler(message: Message):
    await show_bonuses(message)


async def unknown_command(message: Message):
    """
    Обрабатывает неизвестные команды и сообщения
    """
    unknown_text = (
        "🤔 **Неизвестная команда**\n\n"
        "Я не понял, что вы хотите сделать.\n\n"
        "Доступные команды:\n"
        "/start - Начать работу\n"
        "/help - Получить справку\n"
        "/menu - Показать меню\n"
        "/order - Сделать заказ\n"
        "/status - Проверить статус заказа\n"
        "/promo - Применить промокод\n"
        "/random - Случайный набор\n"
        "/bonus - Информация о бонусах\n\n"
        "Или используйте кнопки меню ниже 👇"
    )

    await message.answer(unknown_text, reply_markup=main_keyboard)


# Регистрируем обработчики callback-запросов
async def register_handlers(router):
    """
    Регистрирует все обработчики в роутере
    """
    # Команды
    router.message.register(start_command, Command("start"))
    router.message.register(help_command, Command("help"))
    router.message.register(show_menu, Command("menu"))
    router.message.register(start_order, Command("order"))
    router.message.register(order_status, Command("status"))
    router.message.register(start_promo, Command("promo"))
    router.message.register(random_combo, Command("random"))
    router.message.register(show_bonuses, Command("bonus"))
    router.message.register(use_bonuses_command, Command("use_bonus"))
    router.message.register(promotions, Command("promotions"))

    # Обработчики состояний
    router.message.register(process_size, OrderState.choosing_size)
    router.message.register(process_ingredients, OrderState.choosing_ingredients)
    router.message.register(apply_promo, PromoState.waiting_for_promo)

    # Callback-запросы
    router.callback_query.register(process_payment_callback, F.data.startswith("pay_"))
    router.callback_query.register(check_payment_callback, F.data.startswith("check_payment_"))
    router.callback_query.register(handle_alternative_payment, F.data.startswith("alt_paid_"))

    # Обработчики кнопок
    router.message.register(bonus_button_handler, F.text == "💰 Мои бонусы")
    router.message.register(order_status, F.text == "📦 Статус заказа")
    router.message.register(start_order, F.text == "🍔 Сделать заказ")
    router.message.register(show_menu, F.text == "📋 Меню")
    router.message.register(promotions, F.text == "🎁 Акции и промокоды")
    router.message.register(random_combo, F.text == "🎲 Случайный набор")
    router.message.register(use_bonuses_button, F.text == "💳 Использовать бонусы")
    router.message.register(back_to_menu, F.text == "⬅️ Назад в меню")
    router.message.register(process_bonus_amount, PromoState.waiting_for_bonus_amount)

    # Неизвестные команды (должен быть последним)
    router.message.register(unknown_command)