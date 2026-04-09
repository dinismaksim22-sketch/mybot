import telebot
import time
import re

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"

bot = telebot.TeleBot(TOKEN)

MODS = [7905149857]

users = {}
bans = {}
mutes = {}

# /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if user_id not in users:
        users[user_id] = {"firstSeen": time.time(), "count": 0}

    bot.send_message(user_id,
        "Привет! 👋\n"
        "Добро пожаловать в БУ рынок.\n\n"
        "Отправь объявление.\n"
        "❗Сообщения проверяются модераторами"
    )


# /help
@bot.message_handler(commands=['help'])
def help_cmd(message):
    user_id = message.from_user.id

    if user_id not in MODS:
        bot.send_message(user_id, "❌ Нет доступа.")
        return

    bot.send_message(user_id,
        "🛠 МОДЕРАТОРЫ\n\n"
        "/stats — статистика\n"
        "/ban (reply)\n"
        "/mute 10 (reply)\n"
        "/help"
    )


# /ban
@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    user_id = message.from_user.id

    if user_id not in MODS:
        return

    if not message.reply_to_message:
        return

    match = re.search(r"ID:\s*(\d+)", message.reply_to_message.text or "")
    if not match:
        return

    target_id = int(match.group(1))
    bans[target_id] = True

    bot.send_message(target_id, "⛔ Вас забанили.")


# /mute
@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    user_id = message.from_user.id

    if user_id not in MODS:
        return

    parts = message.text.split()
    if len(parts) < 2:
        return

    if not message.reply_to_message:
        return

    match = re.search(r"ID:\s*(\d+)", message.reply_to_message.text or "")
    if not match:
        return

    minutes = int(parts[1])
    target_id = int(match.group(1))

    mutes[target_id] = time.time() + minutes * 60

    bot.send_message(target_id, "⛔ Мут на " + str(minutes) + " минут")


# /stats
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    user_id = message.from_user.id

    if user_id not in MODS:
        return

    bot.send_message(user_id, "📊 Пользователей: " + str(len(users)))


# все сообщения
@bot.message_handler(func=lambda m: True)
def all_messages(message):
    user_id = message.from_user.id
    text = message.text

    if not text:
        return

    # пропуск команд
    if text.startswith("/"):
        return

    # модеры
    if user_id in MODS:

        if message.reply_to_message:
            match = re.search(r"ID:\s*(\d+)", message.reply_to_message.text or "")
            if match:
                target_id = int(match.group(1))
                bot.send_message(target_id, text)
                return

        for mod in MODS:
            if mod != user_id:
                bot.send_message(
                    mod,
                    "🛡 Модератор @" + str(message.from_user.username or "no_username") + ":\n" + text
                )
        return

    # бан
    if user_id in bans:
        return

    # мут
    if user_id in mutes and time.time() < mutes[user_id]:
        bot.send_message(user_id, "⛔ У вас мут.")
        return

    # регистрация
    if user_id not in users:
        users[user_id] = {"firstSeen": time.time(), "count": 0}

    users[user_id]["count"] += 1

    username = message.from_user.username or "no_username"

    bot.send_message(user_id,
        "⏳ Ожидайте, ваше объявление отправлено на проверку."
    )

    info = (
        "📢 Новое объявление\n\n"
        "👤 @" + username + "\n"
        "🆔 ID: " + str(user_id) + "\n"
        "📨 " + str(users[user_id]["count"])
    )

    for mod in MODS:
        bot.send_message(mod, info)
        bot.forward_message(mod, message.chat.id, message.message_id)


bot.infinity_polling()        return

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
if __name__ == "__main__":
    bot.infinity_polling()
