import telebot
import time
import json
import os
import psycopg2
from telebot import types

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8454142474:AAHuZdNC3N4nVKMXiCCQYNHg1hI9z9njxfI"
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857
CHANNEL_ID = "@br_bu_astana"

# =========================
# POSTGRESQL ПОДКЛЮЧЕНИЕ
# =========================

DATABASE_URL = os.getenv("postgresql://postgres:eCdlxcAddrBPSSeqzSBRfhRLzlLSzXFg@turntable.proxy.rlwy.net:58202/railway")  # <-- ВОТ ТАК ПРАВИЛЬНО

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("❌ DATABASE_URL не задан в переменных окружения")

    return psycopg2.connect(DATABASE_URL)

try:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bot_data (
        key TEXT PRIMARY KEY,
        value JSONB
    )
    """)
    conn.commit()

    print("✅ База данных успешно подключена!")

except Exception as e:
    print(f"❌ Ошибка БД: {e}")
    exit(1)

# =========================
# ЗАГРУЗКА И СОХРАНЕНИЕ
# =========================

def load_data():
    try:
        cursor.execute("SELECT value FROM bot_data WHERE key = 'main'")
        row = cursor.fetchone()
        if row:
            return row[0]
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        
    return {
        "mods": [SUPERADMIN],
        "users": {},
        "usernames": {},
        "bans": [],
        "mutes": {}
    }

# Инициализация глобальных переменных из БД
data = load_data()
MODS = set(data.get("mods", [SUPERADMIN]))
users = data.get("users", {})
usernames = data.get("usernames", {})
bans = set(data.get("bans", []))
mutes = data.get("mutes", {})

def save_data():
    try:
        current_data = {
            "mods": list(MODS),
            "users": users,
            "usernames": usernames,
            "bans": list(bans),
            "mutes": mutes
        }
        cursor.execute("""
        INSERT INTO bot_data (key, value)
        VALUES ('main', %s)
        ON CONFLICT (key)
        DO UPDATE SET value = EXCLUDED.value
        """, (json.dumps(current_data),))
        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        # Если транзакция прервалась, нужно сделать rollback, чтобы следующие запросы не ломались
        conn.rollback()

# =========================
# ВРЕМЕННЫЕ ХРАНИЛИЩА
# =========================
media_groups = {}
pending_posts = {}
waiting_for_reject = {}
waiting_for_msg = {}
waiting_for_broadcast = set()

# =========================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================

def register_user(message):
    uid = str(message.from_user.id)
    uname = message.from_user.username
    if uid not in users:
        users[uid] = {"count": 0}
    if uname:
        usernames[uname.lower()] = int(uid)
    save_data()

def notify_mods(text):
    for m in MODS.union({SUPERADMIN}):
        try:
            bot.send_message(m, text, parse_mode="Markdown")
        except:
            pass

def get_user_id(username_str):
    uname = username_str.replace("@", "").lower()
    return str(usernames.get(uname)) if uname in usernames else None

def mod_kb(post_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("❌ Отказать", callback_data=f"reject_{post_id}"),
        types.InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{post_id}")
    )
    kb.add(types.InlineKeyboardButton("💬 Написать участнику", callback_data=f"msg_{post_id}"))
    return kb

# =========================
# CALLBACK ОБРАБОТЧИК
# =========================

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        data_cb = call.data
        uid = call.from_user.id
        mod_name = call.from_user.username or str(uid)

        if data_cb.startswith("approve_"):
            post_id = data_cb.split("_")[1]
            post = pending_posts.get(post_id)

            if not post:
                bot.answer_callback_query(call.id, "❌ Пост не найден!", show_alert=True)
                return

            # Публикация
            if post["type"] == "album":
                bot.send_media_group(CHANNEL_ID, post["media"])
            else:
                bot.copy_message(CHANNEL_ID, post["chat_id"], post["message_id"])

            bot.send_message(post["user_id"], "✅ Ваше объявление опубликовано!")
            notify_mods(f"✅ Модератор @{mod_name} одобрил пост {post_id}")
            
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            pending_posts.pop(post_id, None)
            bot.answer_callback_query(call.id, "Опубликовано")

        elif data_cb.startswith("reject_"):
            post_id = data_cb.split("_")[1]
            if post_id not in pending_posts:
                return bot.answer_callback_query(call.id, "❌ Пост уже обработан")
            
            waiting_for_reject[uid] = post_id
            bot.send_message(uid, "✍️ Введите причину отказа:")
            bot.answer_callback_query(call.id)

        elif data_cb.startswith("msg_"):
            post_id = data_cb.split("_")[1]
            if post_id not in pending_posts:
                return bot.answer_callback_query(call.id, "❌ Пост уже обработан")

            waiting_for_msg[uid] = post_id
            bot.send_message(uid, "✍️ Введите текст сообщения участнику:")
            bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"Callback error: {e}")

# =========================
# КОМАНДЫ
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message)
    bot.send_message(message.chat.id, "Привет! 👋 Это бот Б/У рынка ASTANA.\nПришли объявление (текст/фото/альбом), указав свой @username.")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    uid = message.from_user.id
    if uid not in MODS and uid != SUPERADMIN: return
    
    text = "🛠 **Админ-панель:**\n/mute @user время причина\n/ban @user\n/stats\n/all (рассылка)"
    if uid == SUPERADMIN:
        text += "\n\n👑 **Создатель:**\n/setadmin @user\n/deladmin @user"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != SUPERADMIN: return
    text = f"📊 Пользователей: {len(users)}\n👮 Модеров: {len(MODS)}\n🚫 Банов: {len(bans)}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['setadmin'])
def set_admin(message):
    if message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    if len(args) < 2: return
    target = get_user_id(args[1])
    if target:
        MODS.add(int(target))
        save_data()
        bot.send_message(message.chat.id, f"✅ {args[1]} теперь модер")

# =========================
# ГЛАВНЫЙ ОБРАБОТЧИК
# =========================

@bot.message_handler(content_types=['text', 'photo', 'video', 'document'])
def handle_docs(message):
    uid = message.from_user.id
    uid_str = str(uid)

    if uid_str in bans: return

    # Проверка мута
    if uid_str in mutes:
        if time.time() < mutes[uid_str]:
            return bot.send_message(uid, "🔇 Вы в муте.")
        else:
            del mutes[uid_str]
            save_data()

    # Рассылка
    if uid == SUPERADMIN and uid in waiting_for_broadcast:
        waiting_for_broadcast.remove(uid)
        for u in users:
            try: bot.copy_message(int(u), message.chat.id, message.message_id)
            except: pass
        return bot.send_message(uid, "✅ Рассылка завершена")

    # Ответ модератора (отказ/сообщение)
    if uid in waiting_for_reject:
        pid = waiting_for_reject.pop(uid)
        post = pending_posts.get(pid)
        if post:
            bot.send_message(post["user_id"], f"❌ Отказ. Причина: {message.text}")
            pending_posts.pop(pid, None)
            bot.send_message(uid, "✅ Отправлено")
        return

    if uid in waiting_for_msg:
        pid = waiting_for_msg.pop(uid)
        post = pending_posts.get(pid)
        if post:
            bot.send_message(post["user_id"], f"💬 Сообщение от админа: {message.text}")
            bot.send_message(uid, "✅ Доставлено")
        return

    # Если пишет админ просто так - пересылаем другим админам (чат)
    if uid in MODS or uid == SUPERADMIN:
        if message.text and message.text.startswith('/'): return # Пропуск команд
        # Логика чата админов (по желанию)

    # ПОДАЧА ОБЪЯВЛЕНИЯ
    register_user(message)
    
    if not message.from_user.username:
        return bot.send_message(uid, "❌ Установите @username в настройках Телеграм!")

    # Обработка альбомов
    if message.media_group_id:
        mid = message.media_group_id
        if mid not in media_groups:
            media_groups[mid] = [message]
            time.sleep(2)
            msgs = media_groups.pop(mid, [])
            
            caption = ""
            album = []
            for m in msgs:
                if m.caption: caption = m.caption
                if m.photo: album.append(types.InputMediaPhoto(m.photo[-1].file_id))
                elif m.video: album.append(types.InputMediaVideo(m.video.file_id))
            
            if "@" not in caption:
                return bot.send_message(uid, "❌ Укажите ваш @username в тексте!")

            album[0].caption = caption
            pid = str(int(time.time() * 1000))
            pending_posts[pid] = {"type": "album", "media": album, "user_id": uid, "chat_id": message.chat.id}
            
            for m_id in MODS.union({SUPERADMIN}):
                try:
                    bot.send_media_group(m_id, album)
                    bot.send_message(m_id, f"📢 Новый альбом от @{message.from_user.username}", reply_markup=mod_kb(pid))
                except: pass
            bot.send_message(uid, "⏳ Отправлено на модерацию")
        else:
            media_groups[mid].append(message)
        return

    # Одиночное сообщение
    else:
        text = message.text or message.caption or ""
        if "@" not in text:
            return bot.send_message(uid, "❌ Укажите @username в тексте!")

        pid = str(int(time.time() * 1000))
        pending_posts[pid] = {
            "type": message.content_type, 
            "user_id": uid, 
            "chat_id": message.chat.id, 
            "message_id": message.message_id
        }

        for m_id in MODS.union({SUPERADMIN}):
            try:
                bot.copy_message(m_id, message.chat.id, message.message_id)
                bot.send_message(m_id, f"📢 Новое от @{message.from_user.username}", reply_markup=mod_kb(pid))
            except: pass
        
        bot.send_message(uid, "⏳ Отправлено на модерацию")

if __name__ == '__main__':
    print("🚀 Бот запущен...")
    bot.infinity_polling()
            
