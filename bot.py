import telebot
import time
import sqlite3
from telebot import types

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8454142474:AAFPX2iAa9FEIAHfLndTbR1h79NZepDJdDs"
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857
DB_FILE = "bot_data.db"
CHANNEL_ID = "@br_bu_astana"

# 🔥 БАЗА ДАННЫХ (SQLITE) 🔥
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Создаем таблицу пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            is_mod INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            mute_until INTEGER DEFAULT 0,
            post_count INTEGER DEFAULT 0
        )
    ''')
    
    # Гарантируем, что SUPERADMIN всегда есть в базе и имеет права
    cursor.execute('''
        INSERT INTO users (user_id, is_mod) 
        VALUES (?, 1) 
        ON CONFLICT(user_id) DO UPDATE SET is_mod=1
    ''', (SUPERADMIN,))
    
    conn.commit()
    conn.close()

init_db()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С БД ---
def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def register_user(message):
    user_id = message.from_user.id
    username = message.from_user.username.lower() if message.from_user.username else None
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, username) 
        VALUES (?, ?) 
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username
    ''', (user_id, username))
    conn.commit()
    conn.close()

def is_mod(user_id):
    if user_id == SUPERADMIN:
        return True
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_mod FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row and row[0] == 1)

def get_all_mods():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE is_mod = 1")
    mods = [row[0] for row in cursor.fetchall()]
    conn.close()
    return set(mods)

def get_user_id_by_username(username_str):
    uname = username_str.replace("@", "").lower()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (uname,))
    row = cursor.fetchone()
    conn.close()
    return str(row[0]) if row else None

def get_user_status(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_banned, mute_until FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"is_banned": bool(row[0]), "mute_until": row[1]}
    return {"is_banned": False, "mute_until": 0}

# Временные операционные хранилища (остаются в памяти, так как это временные состояния)
media_groups = {}
pending_posts = {}
waiting_for_reject = {} 
waiting_for_msg = {}    
waiting_for_broadcast = set() 

def notify_mods(text):
    all_admins = get_all_mods()
    all_admins.add(SUPERADMIN)
    for m in all_admins:
        try:
            bot.send_message(m, text, parse_mode="Markdown")
        except:
            pass

# 🔥 КЛАВИАТУРА МОДЕРАЦИИ
def mod_kb(post_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("❌ Отказать", callback_data=f"reject_{post_id}"),
        types.InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{post_id}")
    )
    kb.add(
        types.InlineKeyboardButton("💬 Написать участнику", callback_data=f"msg_{post_id}")
    )
    return kb

# 🔥 CALLBACK ОБРАБОТЧИК
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        data_cb = call.data
        mod_id = call.from_user.id
        mod_name = call.from_user.username or call.from_user.first_name

        if not is_mod(mod_id):
            return bot.answer_callback_query(call.id, "У вас нет прав!", show_alert=True)

        if data_cb.startswith("approve_"):
            post_id = data_cb.split("_")[1]
            post = pending_posts.get(post_id)

            if not post:
                bot.answer_callback_query(call.id, "❌ Ошибка: Пост не найден в очереди!", show_alert=True)
                return

            bot.answer_callback_query(call.id, "✅ Публикация...")

            try:
                if post["type"] in ["text", "photo", "video"]:
                    bot.copy_message(CHANNEL_ID, post["chat_id"], post["message_id"])
                elif post["type"] == "album":
                    bot.send_media_group(CHANNEL_ID, post["media"])

                try: 
                    bot.send_message(post["user_id"], "✅ Ваше объявление успешно опубликовано!")
                except: 
                    pass
                
                notify_mods(f"✅ Модератор @{mod_name} **одобрил** объявление.")
                
                try: 
                    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                except: 
                    pass
                
                pending_posts.pop(post_id, None)

            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Ошибка отправки в канал: `{e}`", parse_mode="Markdown")

        elif data_cb.startswith("reject_"):
            post_id = data_cb.split("_")[1]
            if post_id not in pending_posts:
                bot.answer_callback_query(call.id, "❌ Пост уже обработан.", show_alert=True)
                return
                
            waiting_for_reject[call.from_user.id] = post_id
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "✍️ Введите причину отказа (будет отправлено пользователю):")

        elif data_cb.startswith("msg_"):
            post_id = data_cb.split("_")[1]
            if post_id not in pending_posts:
                bot.answer_callback_query(call.id, "❌ Пост уже обработан.", show_alert=True)
                return
                
            waiting_for_msg[call.from_user.id] = post_id
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "✍️ Напишите текст сообщения для участника:")

    except Exception as e:
        bot.answer_callback_query(call.id, "⚠️ Системный сбой!", show_alert=True)
        print(f"Callback error: {e}")

# 🔥 КОМАНДА /START
@bot.message_handler(commands=['start'])
def start_command(message):
    register_user(message)
    start_text = (
        "Привет! 👋\n"
        "Ты попал в Б/У рынок ASTANA.\n\n"
        "📌 Для подачи объявления обязательно укажи:\n"
        "1. Куплю / Продам / Набор в ТК или в семью\n"
        "2. Цена / Бюджет\n"
        "3. Контакт (username, пример: @cripta527)\n\n"
        "❗ Важно:\n"
        "Без username заявка будет отклонена.\n"
        "Если ты не указал @username — бот НЕ пропустит объявление.\n\n"
        "🚫 Не спамить\n"
        "Разрешена реклама семьи / СК / ТК и т.д.\n\n"
        "📩 Связь: @cripta527"
    )
    bot.send_message(message.chat.id, start_text)

# 🔥 ПАНЕЛЬ /HELP
@bot.message_handler(commands=['help'])
def help_command(message):
    uid = message.from_user.id
    if not is_mod(uid): 
        return

    text = "🛠 **Панель модератора:**\n"
    text += "🔹 `/id @user` — узнать ID участника\n"
    text += "🔹 `/mute @user время причина` — выдать мут\n"
    text += "🔹 `/unmute @user` — снять мут\n"
    text += "🔹 `/ban @user` — бан навсегда\n"
    text += "🔹 `/unban @user` — разбан\n"
    text += "🔹 `/nlist` — список модераторов\n\n"
    text += "💬 *Все сообщения модераторов в этом чате видят другие модераторы.*\n"

    if uid == SUPERADMIN:
        text += "\n👑 **Команды Создателя:**\n"
        text += "🔸 `/setadmin @user` — выдать права модера\n"
        text += "🔸 `/deladmin @user` — забрать права\n"
        text += "🔸 `/all` — рассылка (фото/видео/текст)\n"
        text += "🔸 `/stats` — статистика\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# 🔥 УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
@bot.message_handler(commands=['id'])
def get_user_id_cmd(message):
    if not is_mod(message.from_user.id): return
        
    args = message.text.split()
    if len(args) < 2:
        return bot.send_message(message.chat.id, "❌ Формат: `/id @user`", parse_mode="Markdown")
    
    target_id = get_user_id_by_username(args[1])
    if target_id: 
        bot.send_message(message.chat.id, f"🔍 ID пользователя {args[1]}: `{target_id}`", parse_mode="Markdown")
    else: 
        bot.send_message(message.chat.id, "❌ Пользователь не найден в базе.")

@bot.message_handler(commands=['mute'])
def mute_command(message):
    if not is_mod(message.from_user.id): return
        
    args = message.text.split(maxsplit=3)
    if len(args) < 3:
        return bot.send_message(message.chat.id, "❌ Формат: `/mute @user время_в_минутах причина`", parse_mode="Markdown")
    
    target_id = get_user_id_by_username(args[1])
    if not target_id: 
        return bot.send_message(message.chat.id, "❌ Пользователь не найден.")
    
    try:
        minutes = int(args[2])
        reason = args[3] if len(args) > 3 else "Не указана"
        mute_timestamp = int(time.time()) + (minutes * 60)
        
        conn = get_db()
        conn.execute("UPDATE users SET mute_until = ? WHERE user_id = ?", (mute_timestamp, target_id))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Пользователь {args[1]} замучен на {minutes} мин.\n📋 Причина: {reason}")
        try: 
            bot.send_message(int(target_id), f"🔇 Вы получили мут на {minutes} минут.\n📋 Причина: {reason}")
        except: 
            pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка: Время должно быть числом.")

@bot.message_handler(commands=['unmute'])
def unmute_command(message):
    if not is_mod(message.from_user.id): return
        
    args = message.text.split()
    if len(args) < 2: 
        return bot.send_message(message.chat.id, "❌ Формат: `/unmute @user`", parse_mode="Markdown")
    
    target_id = get_user_id_by_username(args[1])
    if not target_id:
        return bot.send_message(message.chat.id, "❌ Пользователь не найден.")
        
    conn = get_db()
    conn.execute("UPDATE users SET mute_until = 0 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, f"✅ Мут с пользователя {args[1]} снят.")
    try: 
        bot.send_message(int(target_id), "🔊 Ваш мут был снят.")
    except: 
        pass

@bot.message_handler(commands=['ban'])
def ban_command(message):
    if not is_mod(message.from_user.id): return
        
    args = message.text.split()
    if len(args) < 2: 
        return bot.send_message(message.chat.id, "❌ Формат: `/ban @user`", parse_mode="Markdown")
    
    target_id = get_user_id_by_username(args[1])
    if not target_id: 
        return bot.send_message(message.chat.id, "❌ Пользователь не найден.")
    
    conn = get_db()
    conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, f"✅ Пользователь {args[1]} забанен навсегда.")
    try: 
        bot.send_message(int(target_id), "🚫 Вы были заблокированы в боте.")
    except: 
        pass

@bot.message_handler(commands=['unban'])
def unban_command(message):
    if not is_mod(message.from_user.id): return
        
    args = message.text.split()
    if len(args) < 2: 
        return bot.send_message(message.chat.id, "❌ Формат: `/unban @user`")
    
    target_id = get_user_id_by_username(args[1])
    if not target_id:
        return bot.send_message(message.chat.id, "❌ Пользователь не найден.")
        
    conn = get_db()
    conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, f"✅ Пользователь {args[1]} разбанен.")

@bot.message_handler(commands=['nlist'])
def nlist_command(message):
    if not is_mod(message.from_user.id): return
        
    text = "👮‍♂️ **Список модераторов рынка:**\n\n"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM users WHERE is_mod = 1")
    moderators = cursor.fetchall()
    conn.close()
    
    for i, (mod_id, uname) in enumerate(moderators, 1):
        if uname:
            text += f"{i}. @{uname}\n"
        else:
            text += f"{i}. ID: `{mod_id}` (не найден в базе имен)\n"
            
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# 🔥 КОМАНДЫ ДЛЯ SUPERADMIN
@bot.message_handler(commands=['setadmin'])
def setadmin_command(message):
    if message.from_user.id != SUPERADMIN: return

    args = message.text.split()
    if len(args) < 2:
        return bot.send_message(message.chat.id, "❌ Формат: `/setadmin @user`", parse_mode="Markdown")

    username = args[1].replace("@", "")
    uid = get_user_id_by_username(username)

    if not uid:
        return bot.send_message(message.chat.id, "❌ Юзер не найден. Он должен запустить бота.")

    conn = get_db()
    conn.execute("UPDATE users SET is_mod = 1 WHERE user_id = ?", (uid,))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"✅ @{username} теперь модератор.")
    try:
        bot.send_message(uid, "🎉 Поздравляем! Вы назначены модератором.\n\n📌 Ознакомьтесь с командами: /help")
    except:
        pass


@bot.message_handler(commands=['deladmin'])
def deladmin_command(message):
    if message.from_user.id != SUPERADMIN: return

    args = message.text.split()
    if len(args) < 2:
        return bot.send_message(message.chat.id, "❌ Формат: `/deladmin @user`", parse_mode="Markdown")

    username = args[1].replace("@", "")
    uid = get_user_id_by_username(username)

    if not uid:
        return bot.send_message(message.chat.id, "❌ Юзер не найден.")

    conn = get_db()
    conn.execute("UPDATE users SET is_mod = 0 WHERE user_id = ?", (uid,))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"✅ @{username} снят с должности.")
    try:
        bot.send_message(uid, "⚠️ К сожалению, вы сняты с должности модератора.")
    except:
        pass

@bot.message_handler(commands=['all'])
def broadcast_init(message):
    if message.from_user.id != SUPERADMIN: return
    
    waiting_for_broadcast.add(message.from_user.id)
    bot.send_message(message.chat.id, "📢 **Режим рассылки.**\nОтправьте сообщение (текст, фото или видео) и я разошлю его всем пользователям.", parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    if message.from_user.id != SUPERADMIN: return
        
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_mod = 1")
    total_mods = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    total_bans = cursor.fetchone()[0]
    
    current_time = int(time.time())
    cursor.execute("SELECT COUNT(*) FROM users WHERE mute_until > ?", (current_time,))
    total_mutes = cursor.fetchone()[0]
    
    conn.close()
        
    text = (
        f"📊 **Статистика бота:**\n\n"
        f"👥 Всего в базе: **{total_users}**\n"
        f"👮‍♂️ Модераторов: **{total_mods}**\n"
        f"🚫 Забанено: **{total_bans}**\n"
        f"🔇 В муте: **{total_mutes}**"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('/'))
def unknown_cmd(message):
    bot.send_message(message.chat.id, "❌ Команда не распознана.")

# 🔥📩 ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ (ГЛАВНАЯ ЛОГИКА)
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'voice', 'audio'])
def handle_everything(message):
    uid = message.from_user.id
    user_identity = message.from_user.username or message.from_user.first_name

    # Обработка рассылки /all
    if uid == SUPERADMIN and uid in waiting_for_broadcast:
        waiting_for_broadcast.remove(uid)
        bot.send_message(message.chat.id, "⏳ Рассылка запущена...")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        all_users = cursor.fetchall()
        conn.close()
        
        success_count = 0
        for (target_id,) in all_users:
            try:
                bot.copy_message(target_id, message.chat.id, message.message_id)
                success_count += 1
            except:
                pass
        
        bot.send_message(message.chat.id, f"✅ Рассылка завершена!\nДоставлено: **{success_count}**", parse_mode="Markdown")
        return

    # Обработка причины ОТКАЗА
    if uid in waiting_for_reject:
        post_id = waiting_for_reject.pop(uid)
        reason_text = message.text if message.text else "Причина не указана"
        post_data = pending_posts.get(post_id)
        
        if post_data:
            try:
                bot.send_message(post_data["user_id"], f"❌ **Ваше объявление отклонено!**\n📋 Причина: {reason_text}", parse_mode="Markdown")
            except:
                pass
            notify_mods(f"❌ Модератор @{user_identity} отклонил объявление.\nПричина: {reason_text}")
            pending_posts.pop(post_id, None)
            
        bot.send_message(message.chat.id, "✅ Статус отказа отправлен.")
        return

    # Обработка сообщения УЧАСТНИКУ
    if uid in waiting_for_msg:
        post_id = waiting_for_msg.pop(uid)
        text_for_user = message.text if message.text else "Сообщение без текста"
        post_data = pending_posts.get(post_id)
        
        if post_data:
            try:
                bot.send_message(post_data["user_id"], f"💬 **Сообщение от администрации:**\n{text_for_user}", parse_mode="Markdown")
                bot.send_message(message.chat.id, "✅ Сообщение доставлено.")
            except:
                bot.send_message(message.chat.id, "❌ Не удалось доставить (бот в блоке).")
        return

    # 🛡 ЧАТ МОДЕРАТОРОВ (ВИДЯТ ВСЕ)
    if is_mod(uid):
        all_mods_list = get_all_mods()
        all_mods_list.add(SUPERADMIN)
        for target_mod in all_mods_list:
            if target_mod != uid:
                try:
                    current_mod_tag = f"@{message.from_user.username}" if message.from_user.username else f"ID {uid}"
                    header_msg = f"🛡 Модератор {current_mod_tag}:"
                    
                    bot.send_message(target_mod, header_msg)
                    bot.copy_message(target_mod, message.chat.id, message.message_id)
                except:
                    pass
        return

    # --- ЛОГИКА ДЛЯ ОБЫЧНЫХ ЮЗЕРОВ ---
    register_user(message)
    user_status = get_user_status(uid)

    if user_status["is_banned"]: 
        return
        
    if user_status["mute_until"] > 0:
        if time.time() < user_status["mute_until"]:
            remaining = int((user_status["mute_until"] - time.time()) / 60)
            bot.send_message(uid, f"🔇 Вы в муте. Осталось: {remaining} мин.")
            return
        else:
            # Снимаем мут, если время вышло
            conn = get_db()
            conn.execute("UPDATE users SET mute_until = 0 WHERE user_id = ?", (uid,))
            conn.commit()
            conn.close()

    # Генерация ID поста
    p_id = str(int(time.time() * 1000))

    # Работа с альбомами (ВОССТАНОВЛЕН И ДОПИСАН ОБОРВАННЫЙ КОД)
    if message.media_group_id:
        group_id = message.media_group_id
        if group_id not in media_groups:
            media_groups[group_id] = [message]
            bot.send_message(uid, "Успешно отправлены Медиафайлы. Ожидайте проверки от модераторов, в ближайшее время придет вердикт...")
            time.sleep(2) 
            
            messages_in_group = media_groups.pop(group_id, None)
   
