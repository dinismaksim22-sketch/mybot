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
        bot.send_message(message.chat.id, "❌ Пользователь не найден (пусть напишет боту)")
        return

    uid = usernames[username]
    MODS.add(uid)

    data["mods"] = list(MODS)
    save_data()

    bot.send_message(message.chat.id, f"✅ Вы успешно назначили @{username} модератором")
    bot.send_message(uid, "🎉 Поздравляю! Вы теперь модератор\n\n/help")


# ❌ deladmin
@bot.message_handler(commands=['deladmin'])
def deladmin(message):
    if message.from_user.id != SUPERADMIN:
        return

    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ Используй: /deladmin @username")
        return

    username = args[1].replace("@", "").lower()

    if username not in usernames:
        bot.send_message(message.chat.id, "❌ Пользователь не найден")
        return

    uid = usernames[username]

    if uid in MODS:
        MODS.remove(uid)

        data["mods"] = list(MODS)
        save_data()

        bot.send_message(uid, "❌ К сожалению, вы сняты с должности")
        bot.send_message(message.chat.id, "✅ Вы успешно сняли модератора")


# 📘 help
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id not in MODS:
        return

    bot.send_message(
        message.chat.id,
        "📘 Команды:\n\n"
        "/id @user — узнать ID\n"
        "/mute @user время причина\n"
        "/ban @user причина\n\n"
        "💬 Ответ пользователю: reply на его сообщение"
    )


# 🆔 id
@bot.message_handler(commands=['id'])
def get_id(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ /id @username")
        return

    username = args[1].replace("@", "").lower()

    if username in usernames:
        bot.send_message(message.chat.id, f"🆔 {usernames[username]}")
    else:
        bot.send_message(message.chat.id, "❌ Не найден")


# 🔇 mute
@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    if len(args) < 3:
        bot.send_message(message.chat.id, "❗ /mute @user время причина")
        return

    username = args[1].replace("@", "").lower()
    minutes = int(args[2])
    reason = " ".join(args[3:]) if len(args) > 3 else "Без причины"

    if username not in usernames:
        bot.send_message(message.chat.id, "❌ Не найден")
        return

    uid = usernames[username]
    mutes[uid] = time.time() + minutes * 60

    bot.send_message(uid, f"⛔ Мут {minutes} мин\nПричина: {reason}")

    bot.send_message(
        SUPERADMIN,
        f"‼️ Модератор @{message.from_user.username} выдал мут @{username}\n{reason}"
    )


# 🚫 ban
@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ /ban @user причина")
        return

    username = args[1].replace("@", "").lower()
    reason = " ".join(args[2:]) if len(args) > 2 else "Без причины"

    if username not in usernames:
        bot.send_message(message.chat.id, "❌ Не найден")
        return

    uid = usernames[username]
    bans[uid] = True

    bot.send_message(uid, f"⛔ Вы забанены\nПричина: {reason}")

    bot.send_message(
        SUPERADMIN,
        f"‼️ Модератор @{message.from_user.username} забанил @{username}\n{reason}"
    )


# 📢 all
@bot.message_handler(commands=['all'])
def all_cmd(message):
    if message.from_user.id != SUPERADMIN:
        return

    text = message.text.replace("/all ", "")

    for uid in users:
        try:
            bot.send_message(int(uid), text)
        except:
            pass


# 📩 сообщения (ГЛАВНЫЙ БЛОК)
@bot.message_handler(content_types=['text', 'photo', 'video'])
def all_messages(message):

    if message.text and message.text.startswith("/"):
        return

    register_user(message)

    user_id = message.from_user.id
    text = message.text or message.caption or "📎 Медиа"

    # 👮 модеры
    if user_id in MODS:

        # ответ пользователю
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

        # чат модеров
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

    # отправка модерам (фото/видео)
    for mod in MODS:

        if message.content_type == 'photo':
            bot.send_photo(mod, message.photo[-1].file_id, caption=text)

        elif message.content_type == 'video':
            bot.send_video(mod, message.video.file_id, caption=text)

        else:
            bot.forward_message(mod, message.chat.id, message.message_id)


bot.infinity_polling(skip_pending=True)
