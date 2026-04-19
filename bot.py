import telebot
import time
import json
import os
from telebot import types

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857
CHANNEL_ID = "@br_bu_astana"  # ВСТАВЬ СЮДА СВОЙ КАНАЛ

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

media_groups = {}

# состояния
waiting_reason = {}
waiting_reply = {}
pending_posts = {}


def get_buttons(uid):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("❌ Отказать", callback_data=f"reject_{uid}"),
        types.InlineKeyboardButton("✅ Одобрить", callback_data=f"accept_{uid}")
    )
    markup.add(
        types.InlineKeyboardButton("✍️ Написать сообщение", callback_data=f"reply_{uid}")
    )
    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    mod_id = call.from_user.id
    data = call.data

    if mod_id not in MODS:
        return

    uid = int(data.split("_")[1])

    if data.startswith("reject_"):
        waiting_reason[mod_id] = uid
        bot.send_message(mod_id, "✍️ Напишите причину отказа:")
        bot.answer_callback_query(call.id)

    elif data.startswith("accept_"):
        post = pending_posts.get(uid)

        bot.send_message(uid, "✅ Ваша заявка одобрена и опубликована")

        if post:
            if post["type"] == "text":
                bot.send_message(CHANNEL_ID, post["text"])

            elif post["type"] == "media":
                media = []
                for i, file_id in enumerate(post["files"]):
                    if i == 0:
                        media.append(types.InputMediaPhoto(file_id, caption=post["text"]))
                    else:
                        media.append(types.InputMediaPhoto(file_id))
                bot.send_media_group(CHANNEL_ID, media)

        bot.answer_callback_query(call.id, "Одобрено")

    elif data.startswith("reply_"):
        waiting_reply[mod_id] = uid
        bot.send_message(mod_id, "✍️ Напишите сообщение пользователю:")
        bot.answer_callback_query(call.id)


def register_user(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username

    if user_id not in users:
        users[user_id] = {"count": 0}

    if username:
        usernames[username.lower()] = int(user_id)

    save_data()


@bot.message_handler(commands=['start'])
def start(message):
    register_user(message)

    bot.send_message(
        message.chat.id,
        "Привет! 👋\n"
        "Ты попал в Б/У рынок ASTANA.\n\n"
        "📌 Для подачи объявления обязательно укажи:\n"
        "1. Куплю / Продам / Набор\n"
        "2. Цена\n"
        "3. Контакт (@username)"
    )


@bot.message_handler(commands=['setadmin'])
def setadmin(message):
    if message.from_user.id != SUPERADMIN:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return

    username = message.text.split()[1].replace("@", "").lower()

    if username not in usernames:
        bot.send_message(message.chat.id, "❌ Пользователь не найден")
        return

    uid = usernames[username]
    MODS.add(uid)

    data["mods"] = list(MODS)
    save_data()

    bot.send_message(message.chat.id, f"✅ @{username} теперь модератор")


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

        bot.send_message(message.chat.id, "✅ Готово")

@bot.message_handler(content_types=['text', 'photo', 'video'])
def all_messages(message):

    if message.text and message.text.startswith("/"):
        return

    register_user(message)

    uid = message.from_user.id
    text = message.text or message.caption or "📎 Медиа"

    # МОДЕРЫ
    if uid in MODS:

        if uid in waiting_reason:
            target = waiting_reason.pop(uid)
            bot.send_message(target, f"❌ Ваша заявка отклонена\n\n📌 Причина:\n{text}")
            bot.send_message(uid, "✅ Отказ отправлен")
            return

        if uid in waiting_reply:
            target = waiting_reply.pop(uid)
            bot.send_message(target, f"📩 Сообщение от модератора:\n\n{text}")
            bot.send_message(uid, "✅ Отправлено")
            return

        return

    # проверка username
    if "@" not in text:
        bot.send_message(uid, "❌ Добавь @username")
        return

    if uid in bans:
        return

    if uid in mutes and time.time() < mutes[uid]:
        bot.send_message(uid, "⛔ Мут")
        return

    bot.send_message(uid, "⏳ Заявка отправлена модераторам")

    # АЛЬБОМ
    if message.media_group_id:
        gid = message.media_group_id

        if gid not in media_groups:
            media_groups[gid] = []

        media_groups[gid].append(message)
        time.sleep(1)

        if gid in media_groups:
            msgs = media_groups.pop(gid)

            files = [m.photo[-1].file_id for m in msgs if m.photo]

            pending_posts[uid] = {
                "type": "media",
                "files": files,
                "text": msgs[0].caption or "📎 Медиа"
            }

            for m in MODS:
                bot.send_message(
                    m,
                    f"{text}",
                    reply_markup=get_buttons(uid)
                )
        return

    # обычное сообщение
    pending_posts[uid] = {
        "type": "text",
        "text": text
    }

    for m in MODS:
        bot.send_message(
            m,
            f"{text}",
            reply_markup=get_buttons(uid)
        )


bot.infinity_polling(skip_pending=True)
