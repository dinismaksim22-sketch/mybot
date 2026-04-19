import telebot
import time
import json
import os
from telebot import types

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857

DATA_FILE = "data.json"


# 🔥 ОБНОВЛЕННАЯ ЗАГРУЗКА (С ЗАЩИТОЙ)
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "mods": [SUPERADMIN],
            "users": {},
            "usernames": {}
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

            if not isinstance(data, dict):
                raise Exception("Файл поврежден")

            return data

    except Exception as e:
        print("Ошибка загрузки:", e)

        # пробуем восстановить
        if os.path.exists("data_backup.json"):
            try:
                with open("data_backup.json", "r", encoding="utf-8") as f:
                    print("Восстановление из backup")
                    return json.load(f)
            except:
                pass

        return {
            "mods": [SUPERADMIN],
            "users": {},
            "usernames": {}
        }


# 🔥 ОБНОВЛЕННОЕ СОХРАНЕНИЕ (С BACKUP)
def save_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                old = f.read()

            with open("data_backup.json", "w", encoding="utf-8") as f:
                f.write(old)

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    except Exception as e:
        print("Ошибка сохранения:", e)


data = load_data()

# 🔥 ЗАЩИТА СТРУКТУРЫ
if "mods" not in data:
    data["mods"] = [SUPERADMIN]

if "users" not in data:
    data["users"] = {}

if "usernames" not in data:
    data["usernames"] = {}

MODS = set(data["mods"])
users = data["users"]
usernames = data["usernames"]

bans = {}
mutes = {}

# 🔥 НОВОЕ: хранение медиа-групп
media_groups = {}

# 🔥 ДОБАВЛЕНО
pending_posts = {}
CHANNEL_ID = "@br_bu_astana"


def register_user(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username

    if user_id not in users:
        users[user_id] = {"count": 0}

    if username:
        usernames[username.lower()] = int(user_id)

    save_data()


# 🔥 КНОПКИ
def mod_kb(post_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("❌ Отказать", callback_data=f"reject_{post_id}"),
        types.InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{post_id}")
    )
    kb.add(
        types.InlineKeyboardButton("💬 Написать сообщение", callback_data=f"msg_{post_id}")
    )
    return kb


# 🔥 CALLBACK
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    data_cb = call.data

    if data_cb.startswith("approve_"):
        post_id = data_cb.split("_")[1]
        post = pending_posts.get(post_id)

        if not post:
            return

        if post["type"] == "text":
            bot.copy_message(CHANNEL_ID, post["chat_id"], post["message_id"])

        elif post["type"] == "photo":
            bot.copy_message(CHANNEL_ID, post["chat_id"], post["message_id"])

        elif post["type"] == "album":
            media = []
            for i, m in enumerate(post["messages"]):
                if m.photo:
                    media.append(
                        types.InputMediaPhoto(
                            m.photo[-1].file_id,
                            caption=m.caption if i == 0 else ""
                        )
                    )

            if media:
                bot.send_media_group(CHANNEL_ID, media)

        pending_posts.pop(post_id, None)
        bot.answer_callback_query(call.id, "Одобрено")

    elif data_cb.startswith("reject_"):
        post_id = data_cb.split("_")[1]
        pending_posts.pop(post_id, None)
        bot.answer_callback_query(call.id, "Отклонено")

    elif data_cb.startswith("msg_"):
        bot.answer_callback_query(call.id, "Ответь реплаем на сообщение")


# 👑 /start
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
        "📩 Связь: @cripta527"
    )


# 👑 /setadmin
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


# ❌ /deladmin
@bot.message_handler(commands=['deladmin'])
def deladmin(message):
    if message.from_user.id != SUPERADMIN:
        return

    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ Используй: /deladmin @username")
        return

    username = args[1].replace("@", "").lower()

    if username in usernames:
        uid = usernames[username]

        MODS.discard(uid)
        data["mods"] = list(MODS)
        save_data()

        bot.send_message(uid, "❌ Вы сняты с должности")
        bot.send_message(message.chat.id, "✅ Успешно сняли с должности")


# 📘 /help
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id not in MODS:
        return

    bot.send_message(
        message.chat.id,
        "/id @user\n/mute @user время причина\n/ban @user\n/unmute @user\n/unban @user"
    )


# 🆔 /id
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


# 🔇 /mute
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


# 🚫 /ban
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


# 📢 /all
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


# 🔓 /unmute
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


# 🔓 /unban
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


# 🔥 НОВАЯ КОМАНДА /nlist (СПИСОК МОДЕРОВ)
@bot.message_handler(commands=['nlist'])
def nlist(message):
    if message.from_user.id not in MODS:
        return

    text = "👮‍♂️ Список модераторов:\n\n"

    for i, mod_id in enumerate(MODS, 1):
        uname = None
        for u, uid in usernames.items():
            if uid == mod_id:
                uname = u
                break

        if uname:
            text += f"{i}. @{uname} | ID: {mod_id}\n"
        else:
            text += f"{i}. ID: {mod_id}\n"

    bot.send_message(message.chat.id, text)


# 📩 сообщения
@bot.message_handler(content_types=['text', 'photo', 'video'])
def all_messages(message):

    if message.text and message.text.startswith("/"):
        return

    register_user(message)

    uid = message.from_user.id
    post_id = str(int(time.time() * 1000))

    if uid in bans:
        return

    if uid in mutes and time.time() < mutes[uid]:
        return

    if message.media_group_id:
        gid = message.media_group_id

        if gid not in media_groups:
            media_groups[gid] = []

        media_groups[gid].append(message)
        time.sleep(1)

        msgs = media_groups.pop(gid)

        pending_posts[post_id] = {
            "type": "album",
            "messages": msgs,
            "chat_id": message.chat.id
        }

        for m in MODS:
            bot.send_message(m, "📢 Новое объявление (альбом)", reply_markup=mod_kb(post_id))

        return

    if uid not in MODS:
        if "@" not in (message.text or "") and "@" not in (message.caption or ""):
            bot.send_message(uid, "❌ Добавьте @username")
            return

    bot.send_message(uid, "⏳ Ожидайте проверки")

    pending_posts[post_id] = {
        "type": "photo" if message.photo else "text",
        "chat_id": message.chat.id,
        "message_id": message.message_id
    }

    for m in MODS:
        bot.copy_message(m, message.chat.id, message.message_id)
        bot.send_message(m, "📌 Управление:", reply_markup=mod_kb(post_id))


bot.infinity_polling(skip_pending=True)
