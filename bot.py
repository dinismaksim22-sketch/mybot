import telebot
import time
import json
import os
from telebot import types

TOKEN = os.getenv("8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30")  # вставь токен или через env
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857
CHANNEL_ID = "@br_bu_astana"

DATA_FILE = "data.json"

# ================= DATA =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"mods": [SUPERADMIN], "users": {}, "usernames": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"mods": [SUPERADMIN], "users": {}, "usernames": {}}


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


data = load_data()

MODS = set(data["mods"])
users = data["users"]
usernames = data["usernames"]

bans = {}
mutes = {}

pending_posts = {}
media_groups = {}
reject_reason_wait = {}

# ================= USER =================
def register_user(message):
    uid = str(message.from_user.id)
    username = message.from_user.username

    if uid not in users:
        users[uid] = {"count": 0}

    if username:
        usernames[username.lower()] = int(uid)

    save_data()

# ================= KEYBOARD =================
def mod_kb(post_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("❌ Отказать", callback_data=f"reject_{post_id}"),
        types.InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{post_id}")
    )
    return kb

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    data_cb = call.data

    # ===== APPROVE =====
    if data_cb.startswith("approve_"):
        post_id = data_cb.split("_")[1]
        post = pending_posts.get(post_id)

        if not post:
            return

        # альбом
        if post["type"] == "album":
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

        # одиночное
        elif post["type"] == "single":
            bot.copy_message(CHANNEL_ID, post["chat_id"], post["message_id"])

        pending_posts.pop(post_id, None)
        bot.answer_callback_query(call.id, "Одобрено")

    # ===== REJECT =====
    elif data_cb.startswith("reject_"):
        post_id = data_cb.split("_")[1]
        reject_reason_wait[call.from_user.id] = post_id

        bot.send_message(call.message.chat.id, "✍️ Напишите причину отказа")
        bot.answer_callback_query(call.id)

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    register_user(message)

    bot.send_message(message.chat.id,
        "👋 Добро пожаловать!\n"
        "Отправь объявление (текст / фото / видео)\n"
    )

# ================= HELP =================
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id not in MODS:
        return

    bot.send_message(message.chat.id,
        "/id @user\n"
        "/mute @user минуты причина\n"
        "/unmute @user\n"
        "/ban @user\n"
        "/unban @user\n"
        "/setadmin @user\n"
        "/deladmin @user\n"
        "/all текст"
    )

# ================= ID =================
@bot.message_handler(commands=['id'])
def id_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ /id @user")
        return

    username = args[1].replace("@", "").lower()

    if username in usernames:
        bot.send_message(message.chat.id, str(usernames[username]))
    else:
        bot.send_message(message.chat.id, "❌ Не найден")

# ================= MUTE =================
@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    if len(args) < 3:
        bot.send_message(message.chat.id, "❌ /mute @user минуты причина")
        return

    username = args[1].replace("@", "").lower()
    minutes = int(args[2])
    reason = " ".join(args[3:]) if len(args) > 3 else ""

    if username not in usernames:
        return

    uid = usernames[username]
    mutes[uid] = time.time() + minutes * 60

    bot.send_message(uid, f"🔇 Мут {minutes} мин\n{reason}")
    bot.send_message(message.chat.id, "✅ Заблокирован")

# ================= UNMUTE =================
@bot.message_handler(commands=['unmute'])
def unmute_cmd(message):
    if message.from_user.id not in MODS:
        return

    args = message.text.split()
    username = args[1].replace("@", "").lower()

    if username in usernames:
        mutes.pop(usernames[username], None)
        bot.send_message(message.chat.id, "✅ Размучен")

# ================= BAN =================
@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if message.from_user.id not in MODS:
        return

    username = message.text.split()[1].replace("@", "").lower()

    if username in usernames:
        bans[usernames[username]] = True
        bot.send_message(message.chat.id, "⛔ Забанен")

# ================= UNBAN =================
@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if message.from_user.id not in MODS:
        return

    username = message.text.split()[1].replace("@", "").lower()

    if username in usernames:
        bans.pop(usernames[username], None)
        bot.send_message(message.chat.id, "✅ Разбанен")

# ================= SETADMIN =================
@bot.message_handler(commands=['setadmin'])
def setadmin(message):
    if message.from_user.id != SUPERADMIN:
        return

    username = message.text.split()[1].replace("@", "").lower()

    if username in usernames:
        uid = usernames[username]
        MODS.add(uid)
        data["mods"] = list(MODS)
        save_data()

        bot.send_message(uid, "👮 Вы стали модератором")
        bot.send_message(message.chat.id, "✅ Добавлен")

# ================= DELADMIN =================
@bot.message_handler(commands=['deladmin'])
def deladmin(message):
    if message.from_user.id != SUPERADMIN:
        return

    username = message.text.split()[1].replace("@", "").lower()

    if username in usernames:
        uid = usernames[username]
        MODS.discard(uid)
        data["mods"] = list(MODS)
        save_data()

        bot.send_message(uid, "❌ Вы сняты")
        bot.send_message(message.chat.id, "❌ Удалён")

# ================= ALL =================
@bot.message_handler(commands=['all'])
def all_cmd(message):
    if message.from_user.id != SUPERADMIN:
        return

    text = message.text.replace("/all", "").strip()

    if not text:
        bot.send_message(message.chat.id, "❌ /all текст")
        return

    for uid in users:
        try:
            bot.send_message(int(uid), text)
        except:
            pass

# ================= MAIN MESSAGES =================
@bot.message_handler(content_types=['text', 'photo', 'video'])
def handle(message):

    if message.text and message.text.startswith("/"):
        return

    register_user(message)

    uid = message.from_user.id
    post_id = str(int(time.time() * 1000))

    if uid in bans:
        return

    if uid in mutes and time.time() < mutes[uid]:
        return

    # ===== ALBUM =====
    if message.media_group_id:
        gid = message.media_group_id

        if gid not in media_groups:
            media_groups[gid] = []

        media_groups[gid].append(message)
        time.sleep(1)

        msgs = media_groups.pop(gid)

        pending_posts[post_id] = {
            "type": "album",
            "messages": msgs
        }

        text = "📢 Новое объявление (альбом)\n"
        for m in msgs:
            if m.caption:
                text += m.caption + "\n"

        for mod in MODS:
            bot.send_message(mod, text, reply_markup=mod_kb(post_id))

        return

    # ===== SINGLE =====
    pending_posts[post_id] = {
        "type": "single",
        "chat_id": message.chat.id,
        "message_id": message.message_id
    }

    for mod in MODS:
        bot.copy_message(mod, message.chat.id, message.message_id)
        bot.send_message(mod, "📌 Проверка:", reply_markup=mod_kb(post_id))

# ================= REJECT REASON =================
@bot.message_handler(func=lambda m: m.from_user.id in reject_reason_wait)
def reject_text(message):
    post_id = reject_reason_wait.pop(message.from_user.id)

    post = pending_posts.get(post_id)
    if not post:
        return

    try:
        uid = post.get("user_id")
        if uid:
            bot.send_message(uid, f"❌ Вам отказано\nПричина: {message.text}")
    except:
        pass

    bot.send_message(message.chat.id, "📩 Причина отправлена")

# ================= UNKNOWN COMMAND =================
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/"))
def unknown(message):
    bot.send_message(message.chat.id, "❌ Такой команды нет или нет доступа")

# ================= RUN =================
bot.infinity_polling(skip_pending=True)
