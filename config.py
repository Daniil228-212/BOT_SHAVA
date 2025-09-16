# Настройка ЮKassa
from yookassa import Configuration
# На данный момент, чтобы получить secret_key,
# необходимо пройти верификацию на Юкаасе и зарегистрировать ИП.
# Поэтому из-за недостатка времени решил внедрить оплату по номеру, но в будущем при
# регистрации магазина получении ключа все должно работать отменно.
Configuration.account_id = "shop_id"
Configuration.secret_key = "секретный_ключ"

bot_token = '8286914665:AAHPsw0USNVYzBvt0sjG7H21u2zFz_6mPFk'