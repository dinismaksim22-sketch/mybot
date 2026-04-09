import telebot
import time

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857
MODS = set([SUPERADMIN])

users = {}
bans = {}
mutes = {}

# username -> id (главное хранилище)
usernames = {}


# 📌 универсальная регистрация пользователя
def register_user(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if user_id not in users:
        users[user_id] = {
            "firstSeen": time.time(),
            "count": 0
        }

    # сохраняем username всегда когда он есть
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
        "📌 Отправь объявление по форме.\n"
        "❗ Сообщения проверяются модераторами"
    )


# ВСЕ СООБЩЕНИЯ
@bot.message_handler(content_types=['text', 'photo', 'video'])
def all_messages(message):
    register_user(message)

    user_id = message.from_user.id
    text = message.caption if message.caption else message.text

    if message.text and message.text.startswith("/start"):
        return

    # 👮 МОДЕРАТОРЫ
    if user_id in MODS:

        if message.reply_to_message and message.reply_to_message.text:
            if "ID:" in message.reply_to_message.text:
                target_id = int(message.reply_to_message.text.split("ID:")[1])
                bot.send_message(target_id, text or "📩 Сообщение от модератора")
                return

        for mod in MODS:
            if mod != user_id:
                bot.send_message(
                    mod,
                    f"🛡 Модератор @{message.from_user.username or 'no_username'}:\n{text or '📎 Медиа'}"
                )
        return

    # 🚫 BAN
    if user_id in bans:
        return

    # ⛔ MUTE
    if user_id in mutes and time.time() < mutes[user_id]:
        bot.send_message(user_id, "⛔ У вас мут")
        return

    # регистрация счётчика
    users[user_id]["count"] += 1

    bot.send_message(user_id, "⏳ Ожидайте, объявление отправлено")

    info = f"""📢 Новое объявление
👤 @{message.from_user.username or 'нет_username'}
🆔 ID: {user_id}
📨 {users[user_id]['count']}"""

    for mod in MODS:
        bot.send_message(mod, info)

        if message.content_type == 'photo':
            bot.send_photo(
                mod,
                message.photo[-1].file_id,
                caption=f"👤 @{message.from_user.username or 'нет_username'}\n🆔 ID: {user_id}"
            )

        elif message.content_type == 'video':
            bot.send_video(
                mod,
                message.video.file_id,
                caption=f"👤 @{message.from_user.username or 'нет_username'}\n🆔 ID: {user_id}"
            )

        else:
            bot.forward_message(mod, message.chat.id, message.message_id)


# 👑 SETADMIN (ФИКС 100%)
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
        bot.send_message(
            message.chat.id,
            "❌ Пользователь не найден.\n"
            "Он должен хотя бы 1 раз написать боту /start"
        )
        return

    new_admin_id = usernames[username]
    MODS.add(new_admin_id)

    bot.send_message(message.chat.id, f"✅ @{username} добавлен в модераторы")
    bot.send_message(new_admin_id, "🎉 Вы теперь модератор!")


# 📊 STATS
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id not in MODS:
        return

    bot.send_message(message.chat.id, f"📊 Пользователей: {len(users)}")


# 🚀 запуск
bot.infinity_polling()
