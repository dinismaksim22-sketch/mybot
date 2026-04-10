import telebot
import time

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

SUPERADMIN = 7905149857
MODS = set([SUPERADMIN])

users = {}
usernames = {}

# 📌 регистрация
def register_user(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if user_id not in users:
        users[user_id] = {"count": 0}

    if username:
        usernames[username.lower()] = user_id


# /start
@bot.message_handler(commands=['start'])
def start(message):
    register_user(message)

    bot.send_message(
        message.chat.id,
        "Привет! 👋\n"
        "Ты попал в Б/У рынок ASTANA.\n\n"

        "📌 Для подачи объявления обязательно укажи:\n"
        "1. Куплю / Продам / Набор в ТК или в семью\n"
        "2. Цена / Бюджет\n"
        "3. Контакт (username, пример: @cripta527)\n\n"

        "❗ Важно:\n"
        "Без username заявка будет отклонена.\n"
        "Все пункты должны быть заполнены по форме, иначе будет отказ.\n\n"

        "🚫 Не спамить\n"
        "Разрешена реклама семьи / СК / ТК и т.д.\n\n"

        "📩 Связь: @cripta527"
    )


# 👑 SETADMIN (С DEBUG)
@bot.message_handler(commands=['setadmin'])
def setadmin(message):
    print("SETADMIN CALLED")  # 👈 СМОТРИ В КОНСОЛЬ

    if message.from_user.id != SUPERADMIN:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return

    args = message.text.split()

    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ Используй: /setadmin @username")
        return

    username = args[1].replace("@", "").lower()

    print("TRY ADD:", username)

    if username not in usernames:
        bot.send_message(message.chat.id, "❌ Пользователь не найден")
        return

    new_admin_id = usernames[username]
    MODS.add(new_admin_id)

    bot.send_message(message.chat.id, f"✅ @{username} теперь модератор")
    bot.send_message(new_admin_id, "🎉 Вы теперь модератор!")


# 📩 ВСЕ СООБЩЕНИЯ
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
def all_messages(message):

    # ❗ НЕ ТРОГАЕМ КОМАНДЫ
    if message.text and message.text.startswith("/"):
        return

    register_user(message)

    user_id = message.from_user.id

    bot.send_message(user_id, "⏳ Отправлено модераторам")

    for mod in MODS:
        bot.forward_message(mod, message.chat.id, message.message_id)


# 🚀 ЗАПУСК (КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ)
bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
