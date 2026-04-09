import telebot
import time
import re

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"

bot = telebot.TeleBot(TOKEN)

# 👮 модераторы
MODS = [7905149857]

# базы
users = {}
bans = {}
mutes = {}

# =====================
# /start
# =====================
@bot.message_handler(commands=['start'])
def start(message):
    id = message.from_user.id

    if id not in users:
        users[id] = {
            "firstSeen": time.time(),
            "count": 0
        }

    bot.send_message(id,
"""Привет! 👋
Добро пожаловать в БУ рынок ASTANA.

Отправь объявление.

❗Сообщения проверяются модераторами"""
    )


# =====================
# 🛠 /help (ТОЛЬКО ДЛЯ МОДОВ)
# =====================
@bot.message_handler(commands=['help'])
def help_cmd(message):
    id = message.from_user.id

    if id not in MODS:
        bot.send_message(id, "❌ Нет доступа.")
        return

    bot.send_message(id,
"""🛠 МОДЕРАТОРЫ

/stats — статистика
/ban (reply)
/mute 10 (reply)
/help"""
    )


# =====================
# ⛔ BAN
# =====================
@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    id = message.from_user.id
    if id not in MODS:
        return

    if not message.reply_to_message:
        return

    match = re.search(r"ID:\s*(\d+)", message.reply_to_message.text or "")
    if not match:
        return

    user_id = int(match.group(1))
    bans[user_id] = True

    bot.send_message(user_id, "⛔ Вас забанили.")


# =====================
# ⏳ MUTE
# =====================
@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    id = message.from_user.id
    if id not in MODS:
        return

    parts = message.text.split()
    if len(parts) < 2:
        return

    if not message.reply_to_message:
        return

    match = re.search(r"ID:\s*(\d+)", message.reply_to_message.text or "")
    if not match:
        return

    mins = int(parts[1])
    user_id = int(match.group(1))

    mutes[user_id] = time.time() + mins * 60

    bot.send_message(user_id, f"⛔ Мут на {mins} минут")


# =====================
# 📊 STATS
# =====================
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    id = message.from_user.id

    if id not in MODS:
        return

    bot.send_message(id, f"📊 Пользователей: {len(users)}")


# =====================
# 📩 ВСЕ СООБЩЕНИЯ
# =====================
@bot.message_handler(func=lambda m: True)
def all_messages(message):
    id = message.from_user.id
    text = message.text

    if not text:
        return

    # ❗ ВАЖНО: пропускаем ВСЕ команды
    if text.startswith("/"):
        return

    # =====================
    # 👮 МОДЕРАТОРЫ
    # =====================
    if id in MODS:

        # 💬 ответ пользователю
        if message.reply_to_message:
            match = re.search(r"ID:\s*(\d+)", message.reply_to_message.text or "")

            if match:
                user_id = int(match.group(1))
                bot.send_message(user_id, text)
                return

        # 🛡 чат модеров
        for mod in MODS:
            if mod != id:
                bot.send_message(
                    mod,
                    f"🛡 Модератор @{message.from_user.username or 'no_username'}:\n{text}"
                )
        return

    # =====================
    # 🚫 БАН / МУТ
    # =====================
    if id in bans:
        return

    if id in mutes and time.time() < mutes[id]:
        bot.send_message(id, "⛔ У вас мут.")
        return

    # =====================
    # 👤 РЕГИСТРАЦИЯ
    # =====================
    if id not in users:
        users[id] = {
            "firstSeen": time.time(),
            "count": 0
        }

    users[id]["count"] += 1

    username = message.from_user.username or "no_username"

    # =====================
    # ⏳ автоответ
    # =====================
    bot.send_message(id,
"⏳ Ожидайте, ваше объявление отправлено на проверку."
    )

    # =====================
    # 📢 модерация
    # =====================
    info = f"""📢 Новое объявление

👤 @{username}
🆔 ID: {id}
📨 {users[id]['count']}"""

    for mod in MODS:
        bot.send_message(mod, info)
        bot.forward_message(mod, message.chat.id, message.message_id)


# =====================
# 🚀 ЗАПУСК
# =====================
bot.infinity_polling()
    # модеры
    if id in MODS:

        if message.reply_to_message:
            if "ID:" in message.reply_to_message.text:
                user_id = int(message.reply_to_message.text.split("ID:")[1])
                bot.send_message(user_id, text)
                return

        for mod in MODS:
            if mod != id:
                bot.send_message(mod, f"🛡 Модератор @{message.from_user.username}:\n{text}")
        return

    # бан
    if id in bans:
        return

    # мут
    if id in mutes and time.time() < mutes[id]:
        bot.send_message(id, "⛔ У вас мут")
        return

    # регистрация
    if id not in users:
        users[id] = {
            "firstSeen": time.time(),
            "count": 0
        }

    users[id]["count"] += 1

    bot.send_message(id, "⏳ Ожидайте, объявление отправлено")

    info = f"""📢 Новое объявление
👤 @{message.from_user.username}
🆔 ID: {id}
📨 {users[id]['count']}"""

    for mod in MODS:
        bot.send_message(mod, info)
        bot.forward_message(mod, message.chat.id, message.message_id)

# help
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id not in MODS:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return

    bot.send_message(message.chat.id,
"/ban (reply)\n/mute 10 (reply)\n/stats"
    )

# ban
@bot.message_handler(commands=['ban'])
def ban(message):
    if message.from_user.id not in MODS:
        return

    if message.reply_to_message and "ID:" in message.reply_to_message.text:
        user_id = int(message.reply_to_message.text.split("ID:")[1])
        bans[user_id] = True
        bot.send_message(user_id, "⛔ Вы забанены")

# mute
@bot.message_handler(commands=['mute'])
def mute(message):
    if message.from_user.id not in MODS:
        return

    parts = message.text.split()
    if len(parts) < 2:
        return

    mins = int(parts[1])

    if message.reply_to_message and "ID:" in message.reply_to_message.text:
        user_id = int(message.reply_to_message.text.split("ID:")[1])
        mutes[user_id] = time.time() + mins * 60
        bot.send_message(user_id, f"⛔ Мут на {mins} минут")

# stats
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id not in MODS:
        return

    bot.send_message(message.chat.id, f"📊 Пользователей: {len(users)}")

bot.infinity_polling()
