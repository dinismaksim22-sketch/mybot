import telebot
import time

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857
MODS = set([SUPERADMIN])

users = {}
bans = {}
mutes = {}
usernames = {}


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


# 👑 setadmin
@bot.message_handler(commands=['setadmin'])
def setadmin(message):
    if message.from_user.id != SUPERADMIN:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return

    args = message.text.split()

    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ Используй: /setadmin @username")
        return

    username = args[1].replace("@", "").lower()

    if username not in usernames:
        bot.send_message(message.chat.id, "❌ Пользователь не найден")
        return

    new_admin_id = usernames[username]
    MODS.add(new_admin_id)

    bot.send_message(message.chat.id, f"✅ @{username} теперь модератор")
    bot.send_message(new_admin_id, "🎉 Вы теперь модератор!")


# 📩 ВСЕ СООБЩЕНИЯ
@bot.message_handler(content_types=['text', 'photo', 'video'])
def all_messages(message):

    # ❗ пропускаем команды
    if message.text and message.text.startswith("/"):
        return

    register_user(message)

    user_id = message.from_user.id

    # 👮 МОДЕРАТОРЫ
    if user_id in MODS:

        # 🔥 ОТВЕТ ЧЕРЕЗ FORWARD (НОРМАЛЬНЫЙ СПОСОБ)
        if message.reply_to_message and message.reply_to_message.forward_from:

            target_id = message.reply_to_message.forward_from.id

            bot.send_message(
                target_id,
                f"📩 Модератор ответил:\n{message.text or message.caption or '📎 Медиа'}"
            )
            return

        # 💬 чат модеров
        for mod in MODS:
            if mod != user_id:
                bot.send_message(
                    mod,
                    f"🛡 Модератор @{message.from_user.username or 'no_username'}:\n{message.text or '📎 Медиа'}"
                )

        return

    # 👤 ПОЛЬЗОВАТЕЛЬ

    bot.send_message(user_id, "⏳ Ожидайте, объявление отправлено")

    for mod in MODS:
        # 🔥 ОБЯЗАТЕЛЬНО FORWARD
        bot.forward_message(mod, message.chat.id, message.message_id)


# 🚀 запуск
bot.infinity_polling(skip_pending=True)
