import uuid
from yookassa import Payment
from database import payments, user_orders


async def create_payment(amount, description, user_id, order_id):
    """
    Создает платеж в ЮKassa
    :param amount: Сумма платежа
    :param description: Описание платежа
    :param user_id: ID пользователя
    :param order_id: ID заказа
    :return: Ссылка для оплаты и ID платежа
    """
    idempotence_key = str(uuid.uuid4())

    payment = Payment.create({
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"https://t.me/your_bot_name?start=payment_{user_id}_{order_id}"
        },
        "capture": True,
        "description": description,
        "metadata": {
            "user_id": user_id,
            "order_id": order_id
        }
    }, idempotence_key)

    # Получаемая ссылка для оплаты после регистрации
    confirmation_url = payment.confirmation.confirmation_url
    payment_id = payment.id

    # Сохраняемая информацию о платеже
    payments[payment_id] = {
        "user_id": user_id,
        "order_id": order_id,
        "amount": amount,
        "status": "pending"
    }

    return confirmation_url, payment_id


async def check_payment_status(payment_id):
    """
    Проверяет статус платежа
    :param payment_id: ID платежа
    :return: Статус платежа
    """
    try:
        payment = Payment.find_one(payment_id)
        status = payment.status

        # Обновляем статус в нашем хранилище
        if payment_id in payments:
            payments[payment_id]["status"] = status

            # Если платеж успешен, обновляем статус заказа
            if status == 'succeeded':
                user_id = payments[payment_id]["user_id"]
                order_id = payments[payment_id]["order_id"]

                # Находим заказ и обновляем его статус
                if user_id in user_orders:
                    for order in user_orders[user_id]['orders']:
                        if order.get('number') == order_id:
                            order['status'] = 'В обработке'
                            break

        return status
    except Exception as e:
        print(f"Ошибка при проверке статуса платежа: {e}")
        return 'unknown'