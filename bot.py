import telebot
import time
import json
import os

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857

DATA_FILE = "data.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "mods": [SUPERADMIN],
            "users": {},
            "usernames": {}
        }

    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


data = load_data()

MODS = set(data["mods"])
users = data["users"]
usernames = data["usernames"]

bans = {}
mutes = {}


def register_user(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username

    if user_id not in users:
        users[user_id] = {"count": 0}

    if username:
        usernames[username.lower()] = int(user_id)

    save_data()


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

    uid = usernames[username]
    MODS.add(uid)

    data["mods"] = list(MODS)
    save_data()

    bot.send_message(message.chat.id, f"✅ Вы успешно назначили @{username} модератором")
    bot.send_message(uid, "🎉 Вы теперь модератор\n/help")


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

        data["mods"] = list(MODS)
        save_data()

        bot.send_message(uid, "❌ Вы сняты с должности")
        bot.send_message(message.chat.id, "✅ Готово")


# 🔓 unmute
@bot.message_handler(commands=['unmute'])
def unmute_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    if len(args) < 2:
        return

    username = args[1].replace("@", "").lower()

    if username in usernames:
        uid = usernames[username]

        if uid in mutes:
            del mutes[uid]

        bot.send_message(uid, "✅ С вас снят мут")
        bot.send_message(message.chat.id, "✅ Мут снят")

        bot.send_message(
            SUPERADMIN,
            f"‼️ @{message.from_user.username} снял мут с @{username}"
        )


# 🔓 unban
@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    if len(args) < 2:
        return

    username = args[1].replace("@", "").lower()

    if username in usernames:
        uid = usernames[username]

        if uid in bans:
            del bans[uid]

        bot.send_message(uid, "✅ Вы разбанены")
        bot.send_message(message.chat.id, "✅ Бан снят")

        bot.send_message(
            SUPERADMIN,
            f"‼️ @{message.from_user.username} разбанил @{username}"
        )


# 📩 сообщения
@bot.message_handler(content_types=['text', 'photo', 'video'])
def all_messages(message):

    if message.text and message.text.startswith("/"):
        return

    register_user(message)

    user_id = message.from_user.id
    text = message.text or message.caption or "📎 Медиа"

    # 👮 модеры
    if user_id in MODS:

        if message.reply_to_message and message.reply_to_message.forward_from:

            target = message.reply_to_message.forward_from
            target_username = target.username or "нет_username"

            bot.send_message(
                target.id,
                f"📩 Модератор ответил на ваше сообщение:\n{text}"
            )

            for mod in MODS:
                bot.send_message(
                    mod,
                    f"📤 Ответ пользователю\n"
                    f"👮 @{message.from_user.username}\n"
                    f"👤 @{target_username}\n\n{text}"
                )
            return

        for mod in MODS:
            if mod != user_id:
                bot.send_message(
                    mod,
                    f"🛡 Модератор @{message.from_user.username}:\n{text}"
                )
        return

    # пользователь
    if user_id in bans:
        return

    if user_id in mutes and time.time() < mutes[user_id]:
        bot.send_message(user_id, "⛔ Мут")
        return

    bot.send_message(
        user_id,
        "⏳ Ожидайте, все объявления проверяются модераторами, не нужно дублировать сообщение."
    )

    # 🔥 ВАЖНО: ВСЕ ЧЕРЕЗ FORWARD (будет "переслано от")
    for mod in MODS:
        bot.forward_message(mod, message.chat.id, message.message_id)


bot.infinity_polling(skip_pending=True)
