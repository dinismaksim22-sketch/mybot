import telebot
import time
import json
import os
from telebot import types

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857
DATA_FILE = "data.json"
CHANNEL_ID = "@br_bu_astana"

# 🔥 СТРУКТУРЫ ДАННЫХ
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"mods": [SUPERADMIN], "users": {}, "usernames": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {"mods": [SUPERADMIN], "users": {}, "usernames": {}}
    except:
        return {"mods": [SUPERADMIN], "users": {}, "usernames": {}}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

data = load_data()
MODS = set(data.get("mods", [SUPERADMIN]))
users = data.get("users", {})
usernames = data.get("usernames", {})

# Временные хранилища (в оперативной памяти)
media_groups = {}
pending_posts = {}
waiting_for_reject = {}
waiting_for_msg = {}

def register_user(message):
    user_id = str(message.from_user.id)
    uname = message.from_user.username
    if user_id not in users:
        users[user_id] = {"count": 0}
    if uname:
        usernames[uname.lower()] = int(user_id)
    save_data()

def notify_mods(text):
    for m in MODS:
        try: bot.send_message(m, text, parse_mode="Markdown")
        except: pass

def mod_kb(post_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("❌ Отказать", callback_data=f"rej_{post_id}"),
        types.InlineKeyboardButton("✅ Одобрить", callback_data=f"apr_{post_id}")
    )
    kb.add(types.InlineKeyboardButton("💬 Написать участнику", callback_data=f"msg_{post_id}"))
    return kb

# 🔥 CALLBACK (ИСПРАВЛЕНО: МГНОВЕННЫЙ ОТВЕТ)
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # ПЕРВЫМ ДЕЛОМ ОТВЕЧАЕМ, ЧТОБЫ НЕ БЫЛО ЗАГРУЗКИ
    bot.answer_callback_query(call.id)
    
    try:
        cmd = call.data.split("_")[0]
        post_id = call.data.split("_")[1]
        mod_name = call.from_user.username or call.from_user.first_name
        
        post = pending_posts.get(post_id)

        if not post and cmd != "msg": # Для сообщений можно оставить
            bot.send_message(call.message.chat.id, "⚠️ Ошибка: Пост не найден в памяти бота (возможно, бот перезагружался).")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            return

        if cmd == "apr": # Одобрить
            if post["type"] in ["text", "photo", "video"]:
                bot.copy_message(CHANNEL_ID, post["chat_id"], post["message_id"])
            elif post["type"] == "album":
                bot.send_media_group(CHANNEL_ID, post["media"])
            
            try: bot.send_message(post["user_id"], "✅ Ваше объявление опубликовано!")
            except: pass
            
            notify_mods(f"✅ Модератор @{mod_name} **одобрил** пост `{post_id}`")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            pending_posts.pop(post_id, None)

        elif cmd == "rej": # Отказать
            waiting_for_reject[call.from_user.id] = post_id
            bot.send_message(call.message.chat.id, "📝 Введите причину отказа:")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        elif cmd == "msg": # Написать
            waiting_for_msg[call.from_user.id] = post_id
            bot.send_message(call.message.chat.id, "💬 Введите текст сообщения для пользователя:")

    except Exception as e:
        print(f"Критическая ошибка в кнопках: {e}")

# --- КОМАНДЫ МОДЕРАЦИИ ---

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message)
    bot.send_message(message.chat.id, "👋 Привет! Пришли объявление с @юзернеймом для проверки.")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id not in MODS: return
    bot.send_message(message.chat.id, "🚀 /all [текст] - рассылка\n🚫 /ban @user - бан\n🔇 /mute @user [мин] [причина]\n👮‍♂️ /nlist - админы")

@bot.message_handler(commands=['all'])
def all_cmd(message):
    if message.from_user.id != SUPERADMIN: return
    text = message.text.replace("/all", "").strip()
    if not text:
        bot.send_message(message.chat.id, "❌ Ошибка: напишите текст. Пример: `/all Всем привет`", parse_mode="Markdown")
        return
    for u in users:
        try: bot.send_message(int(u), text)
        except: pass
    bot.send_message(message.chat.id, "✅ Рассылка завершена.")

@bot.message_handler(commands=['nlist'])
def nlist(message):
    if message.from_user.id not in MODS: return
    res = "👮‍♂️ Модераторы:\n" + "\n".join([f"• `{m}`" for m in MODS])
    bot.send_message(message.chat.id, res, parse_mode="Markdown")

# 🔥 ОБРАБОТКА НЕИЗВЕСТНЫХ КОМАНД
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/") and m.text.split()[0][1:] not in ['start', 'help', 'all', 'mute', 'ban', 'unmute', 'unban', 'nlist', 'id', 'setadmin', 'deladmin'])
def unknown(m):
    bot.send_message(m.chat.id, "❓ Команда не существует или недоступна.")

# 🔥 ОСНОВНОЙ ОБРАБОТЧИК
@bot.message_handler(content_types=['text', 'photo', 'video'])
def handle_docs(message):
    uid = message.from_user.id
    
    # Стейт: Причина отказа
    if uid in waiting_for_reject:
        post_id = waiting_for_reject.pop(uid)
        post = pending_posts.pop(post_id, None)
        if post:
            try: bot.send_message(post["user_id"], f"❌ Вам отказано.\nПричина: {message.text}")
            except: pass
            notify_mods(f"❌ Модератор @{message.from_user.username} отказал посту `{post_id}`. Причина: {message.text}")
        return

    # Стейт: Сообщение юзеру
    if uid in waiting_for_msg:
        post_id = waiting_for_msg.pop(uid)
        post = pending_posts.get(post_id)
        if post:
            try: bot.send_message(post["user_id"], f"💬 Сообщение от модератора:\n{message.text}")
            except: pass
            bot.send_message(uid, "✅ Отправлено.")
        return

    # Чат модеров
    if uid in MODS and not message.media_group_id:
        if not message.text or not message.text.startswith("/"):
            for m in MODS:
                if m != uid:
                    try: bot.send_message(m, f"👮‍♂️ **@{message.from_user.username}:**\n{message.text}", parse_mode="Markdown")
                    except: pass
            if not message.text: pass # если это медиа для поста, идем дальше
            else: return

    # Проверка бана/мута
    if uid in bans: return
    # (Тут можно добавить проверку mutes)

    # Подача объявления
    post_id = str(int(time.time() * 100))
    
    if message.media_group_id:
        gid = message.media_group_id
        if gid not in media_groups:
            media_groups[gid] = [message]
            time.sleep(1.5) # Ждем сбора альбома
            msgs = media_groups.pop(gid)
            
            media = []
            for i, m in enumerate(msgs):
                cap = m.caption if i == 0 else ""
                if i == 0 and "@" not in (cap or ""):
                    bot.send_message(uid, "❌ Ошибка: Забыли указать @username в описании.")
                    return
                if m.photo: media.append(types.InputMediaPhoto(m.photo[-1].file_id, caption=cap))
                elif m.video: media.append(types.InputMediaVideo(m.video.file_id, caption=cap))

            pending_posts[post_id] = {"type": "album", "media": media, "user_id": uid, "chat_id": message.chat.id}
            bot.send_message(uid, "⏳ Альбом на проверке.")
            for m in MODS:
                bot.send_media_group(m, media)
                bot.send_message(m, f"📢 Альбом от `{uid}`", reply_markup=mod_kb(post_id), parse_mode="Markdown")
        else:
            media_groups[gid].append(message)
        return

    # Одиночное сообщение
    if "@" not in (message.text or message.caption or ""):
        bot.send_message(uid, "❌ Ошибка: Укажите ваш @username в тексте!")
        return

    pending_posts[post_id] = {
        "type": "photo" if message.photo else ("video" if message.video else "text"),
        "user_id": uid, "chat_id": message.chat.id, "message_id": message.message_id
    }
    bot.send_message(uid, "⏳ Объявление отправлено на модерацию.")
    for m in MODS:
        bot.copy_message(m, message.chat.id, message.message_id)
        bot.send_message(m, f"📢 Пост от `{uid}`", reply_markup=mod_kb(post_id), parse_mode="Markdown")

bot.infinity_polling()
