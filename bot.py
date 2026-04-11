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
        return

    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ /setadmin @username")
        return

    username = args[1].replace("@", "").lower()

    if username not in usernames:
        bot.send_message(message.chat.id, "❌ Пользователь не найден")
        return

    new_id = usernames[username]
    MODS.add(new_id)

    bot.send_message(message.chat.id, "✅ Модератор добавлен")

    bot.send_message(
        new_id,
        "🎉 Поздравляю! Вы теперь модератор.\n\n"
        "Введите /help"
    )


# ❌ deladmin
@bot.message_handler(commands=['deladmin'])
def deladmin(message):
    if message.from_user.id != SUPERADMIN:
        return

    args = message.text.split()
    if len(args) < 2:
        return

    username = args[1].replace("@", "").lower()

    if username in usernames:
        uid = usernames[username]
        MODS.discard(uid)

        bot.send_message(uid, "❌ Вы сняты с должности")
        bot.send_message(message.chat.id, "✅ Модератор удалён")


# 📘 help
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id not in MODS:
        return

    bot.send_message(
        message.chat.id,
        "/id @user\n"
        "/mute @user время причина\n"
        "/ban @user причина\n"
    )


# 🔇 mute
@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    if len(args) < 3:
        return

    username = args[1].replace("@", "").lower()
    minutes = int(args[2])
    reason = " ".join(args[3:]) if len(args) > 3 else "Без причины"

    if username not in usernames:
        return

    user_id = usernames[username]
    mutes[user_id] = time.time() + minutes * 60

    bot.send_message(user_id, f"⛔ Мут {minutes} мин\nПричина: {reason}")

    # 🔥 ЛОГ ТЕБЕ
    bot.send_message(
        SUPERADMIN,
        f"‼️ Модератор @{message.from_user.username} выдал мут пользователю @{username}\n"
        f"⏱ {minutes} мин\n📄 {reason}"
    )


# 🚫 ban
@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    if len(args) < 2:
        return

    username = args[1].replace("@", "").lower()
    reason = " ".join(args[2:]) if len(args) > 2 else "Без причины"

    if username not in usernames:
        return

    user_id = usernames[username]
    bans[user_id] = True

    bot.send_message(user_id, f"⛔ Вы забанены\nПричина: {reason}")

    # 🔥 ЛОГ ТЕБЕ
    bot.send_message(
        SUPERADMIN,
        f"‼️ Модератор @{message.from_user.username} забанил пользователя @{username}\n"
        f"📄 {reason}"
    )


# 📢 all
@bot.message_handler(commands=['all'])
def broadcast(message):
    if message.from_user.id != SUPERADMIN:
        return

    text = message.text.replace("/all ", "")

    for uid in users:
        try:
            bot.send_message(uid, f"📢 {text}")
        except:
            pass


# 📩 сообщения
@bot.message_handler(content_types=['text'])
def all_messages(message):

    if message.text.startswith("/"):
        return

    register_user(message)

    user_id = message.from_user.id

    # 👮 модеры
    if user_id in MODS:

        if message.reply_to_message and message.reply_to_message.forward_from:
            target = message.reply_to_message.forward_from

            bot.send_message(
                target.id,
                f"📩 Модератор ответил:\n{message.text}"
            )

            return

        return

    # пользователь
    bot.send_message(user_id, "⏳ Отправлено")

    for mod in MODS:
        bot.forward_message(mod, message.chat.id, message.message_id)


bot.infinity_polling(skip_pending=True)
