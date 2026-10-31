import os

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# Список услуг
SERVICES = {
    "haircut": "Стрижка (1500 ₽)",
    "beard": "Борода (1000 ₽)",
    "complex": "Стрижка + Борода (2000 ₽)"
}

# СПИСОК МАСТЕРОВ (Можно менять)
MASTERS = {
    "alex": "Александр",
    "dmitry": "Дмитрий",
    "ivan": "Иван"
}

TEXTS = {
    "start": "💈 Добро пожаловать в барбершоп!\nВыберите действие:",
    "choose_service": "Выберите услугу:",
    "choose_master": "К какому мастеру хотите записаться?",
    "enter_name": "Введите ваше имя:",
    "enter_time": "Введите желаемую дату и время (например: 25.10 в 15:00):",
    "success": "✅ Спасибо, {name}! Вы записаны на {service} к мастеру {master} на {time}.\nМы свяжемся с вами для подтверждения.",
}
