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

    bot.send_message(
        new_admin_id,
        "🎉 Поздравляю! Вы теперь модератор.\n\n"
        "📘 Ознакомьтесь с командами:\n"
        "/help"
    )


# 📘 HELP
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id not in MODS:
        return

    bot.send_message(
        message.chat.id,
        "📘 Команды модератора:\n\n"
        "/id @username — узнать ID пользователя\n"
        "/mute @username время(мин) причина — выдать мут\n"
        "/ban @username причина — забанить\n\n"
        "💬 Ответ пользователю:\n"
        "Просто ответь (reply) на его сообщение"
    )


# 🆔 ID
@bot.message_handler(commands=['id'])
def get_id(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()

    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ Используй: /id @username")
        return

    username = args[1].replace("@", "").lower()

    if username in usernames:
        bot.send_message(message.chat.id, f"🆔 ID @{username}: {usernames[username]}")
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден")


# 🔇 MUTE
@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()

    if len(args) < 3:
        bot.send_message(message.chat.id, "❗ /mute @username время причина")
        return

    username = args[1].replace("@", "").lower()
    minutes = int(args[2])
    reason = " ".join(args[3:]) if len(args) > 3 else "Без причины"

    if username not in usernames:
        bot.send_message(message.chat.id, "❌ Пользователь не найден")
        return

    user_id = usernames[username]
    mutes[user_id] = time.time() + minutes * 60

    bot.send_message(user_id, f"⛔ Вам выдан мут на {minutes} мин\nПричина: {reason}")
    bot.send_message(message.chat.id, "✅ Мут выдан")


# 🚫 BAN
@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()

    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ /ban @username причина")
        return

    username = args[1].replace("@", "").lower()
    reason = " ".join(args[2:]) if len(args) > 2 else "Без причины"

    if username not in usernames:
        bot.send_message(message.chat.id, "❌ Пользователь не найден")
        return

    user_id = usernames[username]
    bans[user_id] = True

    bot.send_message(user_id, f"⛔ Вы забанены\nПричина: {reason}")
    bot.send_message(message.chat.id, "✅ Пользователь забанен")


# 📩 ВСЕ СООБЩЕНИЯ
@bot.message_handler(content_types=['text', 'photo', 'video'])
def all_messages(message):

    if message.text and message.text.startswith("/"):
        return

    register_user(message)

    user_id = message.from_user.id

    # 👮 МОДЕРЫ
    if user_id in MODS:

        # ответ пользователю
        if message.reply_to_message and message.reply_to_message.forward_from:
            target_id = message.reply_to_message.forward_from.id

            bot.send_message(
                target_id,
                f"📩 Модератор ответил:\n{message.text or message.caption or '📎 Медиа'}"
            )
            return

        # чат модеров
        for mod in MODS:
            if mod != user_id:
                bot.send_message(
                    mod,
                    f"🛡 Модератор @{message.from_user.username}:\n{message.text or '📎 Медиа'}"
                )
        return

    # 🚫 бан
    if user_id in bans:
        return

    # ⛔ мут
    if user_id in mutes and time.time() < mutes[user_id]:
        bot.send_message(user_id, "⛔ У вас мут")
        return

    bot.send_message(user_id, "⏳ Ожидайте, объявление отправлено")

    # отправка модерам
    for mod in MODS:
        bot.forward_message(mod, message.chat.id, message.message_id)


# 🚀 запуск
bot.infinity_polling(skip_pending=True)
