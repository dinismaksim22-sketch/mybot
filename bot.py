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
        bot.send_message(message.chat.id, "❗ /setadmin @username")
        return

    username = args[1].replace("@", "").lower()

    if username not in usernames:
        bot.send_message(message.chat.id, "❌ Пользователь не найден")
        return

    uid = usernames[username]
    MODS.add(uid)

    data["mods"] = list(MODS)
    save_data()

    bot.send_message(message.chat.id, f"✅ @{username} теперь модератор")
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


# 📘 help
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id not in MODS:
        return

    bot.send_message(
        message.chat.id,
        "/id @user\n/mute @user время причина\n/ban @user причина\n/unmute @user\n/unban @user"
    )


# 🆔 id
@bot.message_handler(commands=['id'])
def get_id(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    if len(args) < 2:
        return

    username = args[1].replace("@", "").lower()

    if username in usernames:
        bot.send_message(message.chat.id, str(usernames[username]))


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
    reason = " ".join(args[3:]) if len(args) > 3 else ""

    if username not in usernames:
        return

    uid = usernames[username]
    mutes[uid] = time.time() + minutes * 60

    bot.send_message(uid, f"⛔ Мут {minutes} мин\n{reason}")


# 🚫 ban
@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    if len(args) < 2:
        return

    username = args[1].replace("@", "").lower()

    if username not in usernames:
        return

    uid = usernames[username]
    bans[uid] = True

    bot.send_message(uid, "⛔ Вы забанены")


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


# 🔓 UNMUTE (ДОБАВЛЕНО)
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
        mutes.pop(uid, None)

        bot.send_message(uid, "✅ Мут снят")
        bot.send_message(message.chat.id, "✅ Ок")


# 🔓 UNBAN (ДОБАВЛЕНО)
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
        bans.pop(uid, None)

        bot.send_message(uid, "✅ Вы разбанены")
        bot.send_message(message.chat.id, "✅ Ок")


# 📩 СООБЩЕНИЯ (ИСПРАВЛЕНО МЕДИА + ПЕРЕСЫЛКА)
@bot.message_handler(content_types=['text', 'photo', 'video'])
def all_messages(message):

    if message.text and message.text.startswith("/"):
        return

    register_user(message)

    uid = message.from_user.id
    text = message.text or message.caption or "📎 Медиа"

    # 👮 МОДЕРЫ
    if uid in MODS:

        if message.reply_to_message and message.reply_to_message.forward_from:

            target = message.reply_to_message.forward_from

            bot.send_message(
                target.id,
                f"📩 Модератор ответил:\n{text}"
            )

            for m in MODS:
                bot.send_message(
                    m,
                    f"📤 @{message.from_user.username} → @{target.username}\n{text}"
                )
            return

        for m in MODS:
            if m != uid:
                bot.send_message(
                    m,
                    f"🛡 Модератор @{message.from_user.username}:\n{text}"
                )
        return

    # ❌ BAN
    if uid in bans:
        return

    # ❌ MUTE
    if uid in mutes and time.time() < mutes[uid]:
        bot.send_message(uid, "⛔ Мут")
        return

    bot.send_message(
        uid,
        "⏳ Ожидайте, все объявления проверяются модераторами."
    )

    # 📩 ВАЖНО: ВСЕ МЕДИА КАК ПЕРЕСЛАНОЕ (с 'Переслано от')
    for m in MODS:
        bot.forward_message(m, message.chat.id, message.message_id)


bot.infinity_polling(skip_pending=True)
