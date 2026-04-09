import telebot
import time

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"

bot = telebot.TeleBot(TOKEN)

# 👑 ТЫ (главный админ)
SUPERADMIN = 7905149857

# 👮 модераторы
MODS = set([SUPERADMIN])

# username -> id
usernames = {}

users = {}
bans = {}
mutes = {}

# /start
@bot.message_handler(commands=['start'])
def start(message):
    id = message.from_user.id

    if id not in users:
        users[id] = {
            "firstSeen": time.time(),
            "count": 0
        }

    # сохраняем username
    if message.from_user.username:
        usernames[message.from_user.username.lower()] = id

    bot.send_message(
        id,
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


# ВСЕ СООБЩЕНИЯ (текст + фото + видео)
@bot.message_handler(content_types=['text', 'photo', 'video'])
def all_messages(message):
    id = message.from_user.id
    text = message.caption if message.caption else message.text

    if message.text and message.text.startswith("/start"):
        return

    # МОДЕРАТОРЫ
    if id in MODS:

        if message.reply_to_message and message.reply_to_message.text:
            if "ID:" in message.reply_to_message.text:
                user_id = int(message.reply_to_message.text.split("ID:")[1])
                bot.send_message(user_id, text or "📩 Сообщение от модератора")
                return

        for mod in MODS:
            if mod != id:
                bot.send_message(
                    mod,
                    f"🛡 Модератор @{message.from_user.username}:\n{text or '📎 Медиа'}"
                )
        return

    # БАН
    if id in bans:
        return

    # МУТ
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

        if message.content_type == 'photo':
            bot.send_photo(
                mod,
                message.photo[-1].file_id,
                caption=f"👤 @{message.from_user.username}\n🆔 ID: {id}"
            )

        elif message.content_type == 'video':
            bot.send_video(
                mod,
                message.video.file_id,
                caption=f"👤 @{message.from_user.username}\n🆔 ID: {id}"
            )

        else:
            bot.forward_message(mod, message.chat.id, message.message_id)


# 👑 SETADMIN (по username)
@bot.message_handler(commands=['setadmin'])
def setadmin(message):
    if message.from_user.id != SUPERADMIN:
        bot.send_message(message.chat.id, "❌ Только главный админ может назначать модераторов")
        return

    parts = message.text.split()

    if len(parts) < 2:
        bot.send_message(message.chat.id, "Используй: /setadmin @username")
        return

    username = parts[1].replace("@", "").lower()

    if username in usernames:
        new_admin_id = usernames[username]
        MODS.add(new_admin_id)

        bot.send_message(message.chat.id, f"✅ @{username} теперь модератор")
        bot.send_message(new_admin_id, "🎉 Вас назначили модератором!")
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден или не писал боту")


# HELP
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id not in MODS:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return

    bot.send_message(
        message.chat.id,
        "/ban (reply)\n/mute 10 (reply)\n/stats\n/setadmin @username"
    )


# BAN
@bot.message_handler(commands=['ban'])
def ban(message):
    if message.from_user.id not in MODS:
        return

    if message.reply_to_message and "ID:" in message.reply_to_message.text:
        user_id = int(message.reply_to_message.text.split("ID:")[1])
        bans[user_id] = True
        bot.send_message(user_id, "⛔ Вы забанены")


# MUTE
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


# STATS
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id not in MODS:
        return

    bot.send_message(message.chat.id, f"📊 Пользователей: {len(users)}")


bot.infinity_polling()
