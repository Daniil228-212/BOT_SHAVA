from datetime import datetime
from database import user_bonuses, loyalty_levels


def check_order_status(order):
    current_time = datetime.now()

    if isinstance(order, dict) and 'status' in order:
        if order['status'] in ['В обработке', 'В обработке (альтернативная)'] and current_time >= order[
            'estimated_time']:
            order['status'] = '✅ Готов к выдаче'
        elif order['status'] == 'Ожидает оплаты (альтернативная)':
            pass

    return order


def calculate_level(total_spent):
    """
    Определяет уровень лояльности на основе потраченной суммы
    """
    current_level = 'bronze'  # Уровень по умолчанию

    # Сортируем уровни по минимальной сумме в порядке возрастания
    sorted_levels = sorted(loyalty_levels.items(), key=lambda x: x[1]['min_spent'])

    for level, info in sorted_levels:
        if total_spent >= info['min_spent']:
            current_level = level

    return current_level


async def add_bonuses(user_id, order_amount, bonus_earned):
    """
    Добавляет бонусы и обновляет общую сумму потраченных средств
    """
    if user_id not in user_bonuses:
        user_bonuses[user_id] = {
            'bonus_points': 0,
            'total_spent': 0,
            'loyalty_level': 'bronze',
            'cashback_earned': 0
        }

    # Обновляем общую сумму потраченных средств
    user_bonuses[user_id]['total_spent'] += order_amount
    user_bonuses[user_id]['bonus_points'] += bonus_earned
    user_bonuses[user_id]['cashback_earned'] += bonus_earned

    # Пересчитываем уровень лояльности
    user_bonuses[user_id]['loyalty_level'] = calculate_level(user_bonuses[user_id]['total_spent'])


def format_time_remaining(estimated_time):
    """
    Форматирует оставшееся время до готовности заказа
    """
    current_time = datetime.now()
    time_diff = estimated_time - current_time

    if time_diff.total_seconds() <= 0:
        return "готов ✅"

    minutes = int(time_diff.total_seconds() // 60)
    seconds = int(time_diff.total_seconds() % 60)

    if minutes < 1:
        return f"{seconds} сек"
    elif minutes < 60:
        return f"{minutes} мин"
    else:
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours} ч {minutes} мин"

def calculate_discount_price(original_price, discount_percent):
    """
    Рассчитывает цену со скидкой
    """
    discount_amount = original_price * discount_percent // 100
    return original_price - discount_amount, discount_amount


def validate_ingredients(ingredients_list):
    """
    Проверяет валидность выбранных ингредиентов
    """
    valid_ingredients = {
        'говядина', 'креветки', 'свинина', 'курица', 'салат', 'помидор',
        'огурец', 'корейская морковка', 'красный лук', 'перец',
        'классический(майонез-кетчуп)', 'острый чили', 'чесночный',
        'сырный', 'брусничный', 'кисло-сладкий', 'тофу', 'маринованные овощи'
    }

    invalid_ingredients = []
    valid_ingredients_found = []

    for ing in ingredients_list:
        if ing.strip().lower() in valid_ingredients:
            valid_ingredients_found.append(ing.strip().lower())
        else:
            invalid_ingredients.append(ing)

    return valid_ingredients_found, invalid_ingredients


def generate_order_summary(order_data):
    """
    Генерирует текстовую сводку заказа
    """
    summary = f"Заказ #{order_data['number']}\n"
    summary += f"Состав: {', '.join(order_data['items'])}\n"
    summary += f"Стоимость: {order_data['final_price']}₽\n"

    if order_data.get('discount_applied'):
        summary += f"Скидка: {order_data['discount_amount']}₽\n"

    if order_data.get('bonus_applied'):
        summary += f"Оплачено бонусами: {order_data['bonus_amount']}₽\n"

    summary += f"Статус: {order_data['status']}\n"

    if 'estimated_time' in order_data:
        summary += f"Время готовности: {order_data['estimated_time'].strftime('%H:%M')}\n"

    return summary


def calculate_bonus_percentage(level):
    """
    Возвращает процент кэшбека для уровня лояльности
    """
    return loyalty_levels.get(level, {}).get('cashback', 5)


def get_next_level_info(current_level, total_spent):
    """
    Возвращает информацию о следующем уровне лояльности
    """
    levels = list(loyalty_levels.keys())
    current_index = levels.index(current_level) if current_level in levels else 0

    if current_index < len(levels) - 1:
        next_level = levels[current_index + 1]
        next_level_info = loyalty_levels[next_level]
        needed = next_level_info['min_spent'] - total_spent
        return next_level, next_level_info, needed

    return None, None, 0


def format_bonus_history(bonus_transactions):
    """
    Форматирует историю бонусных операций
    """
    if not bonus_transactions:
        return "История бонусных операций пуста"

    history_text = "📋 История бонусных операций:\n\n"
    for i, transaction in enumerate(bonus_transactions, 1):
        history_text += f"{i}. {transaction['date']} - {transaction['amount']}₽ - {transaction['type']}\n"
        if transaction.get('description'):
            history_text += f"   {transaction['description']}\n"
        history_text += "\n"

    return history_text


def calculate_max_bonus_usage(order_price, available_bonuses):
    """
    Рассчитывает максимальное количество бонусов, которое можно использовать
    """
    max_from_order = order_price * 50 // 100  # Максимум 50% от заказа
    return min(available_bonuses, max_from_order)