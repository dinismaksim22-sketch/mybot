import telebot
import time

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"

bot = telebot.TeleBot(TOKEN)

MODS = [7905149857]  # сюда свой ID

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

# все сообщения
@bot.message_handler(func=lambda m: True)
def all_messages(message):
    id = message.from_user.id
    text = message.text

    if not text or text.startswith("/start"):
        return

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
