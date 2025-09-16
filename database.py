# База данных для промокодов
user_orders = {}
user_promos = {}
promo_codes = {"STUDENT": 10, "KING": 20, "HPB": 30}
payments = {}  # Хранение информации о платежах

# Система бонусов и уровней лояльности
user_bonuses = {}
loyalty_levels = {
    "bronze": {"min_spent": 0, "cashback": 5, "min_discount": 5},
    "silver": {"min_spent": 2000, "cashback": 7, "min_discount": 10},
    "gold": {"min_spent": 5000, "cashback": 10, "min_discount": 15},
    "platinum": {"min_spent": 10000, "cashback": 15, "min_discount": 20}
}