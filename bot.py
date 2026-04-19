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
            if not isinstance(data, dict):
                raise Exception("Файл поврежден")
            return data
    except Exception as e:
        print("Ошибка загрузки:", e)
        if os.path.exists("data_backup.json"):
            try:
                with open("data_backup.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"mods": [SUPERADMIN], "users": {}, "usernames": {}}

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

if "mods" not in data: data["mods"] = [SUPERADMIN]
if "users" not in data: data["users"] = {}
if "usernames" not in data: data["usernames"] = {}

MODS = set(data["mods"])
users = data["users"]
usernames = data["usernames"]

bans = {}
mutes = {}

# Временные хранилища
media_groups = {}
pending_posts = {}
waiting_for_reject = {} # Хранит id модератора -> post_id
waiting_for_msg = {}    # Хранит id модератора -> post_id

def register_user(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    if user_id not in users:
        users[user_id] = {"count": 0}
    if username:
        usernames[username.lower()] = int(user_id)
    save_data()

def notify_mods(text):
    """Рассылка системных уведомлений всем модераторам"""
    for m in MODS:
        try:
            bot.send_message(m, text)
        except:
            pass

# 🔥 КНОПКИ
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

# 🔥 CALLBACK (Кнопки) - ИСПРАВЛЕНА ВЕЧНАЯ ЗАГРУЗКА
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        data_cb = call.data
        mod_name = call.from_user.username or call.from_user.first_name
        chat_id = call.message.chat.id
        msg_id = call.message.message_id

        if data_cb.startswith("approve_"):
            post_id = data_cb.split("_")[1]
            post = pending_posts.get(post_id)

            if not post:
                bot.answer_callback_query(call.id, "❌ Заявка устарела (после перезапуска бота) или уже обработана другим модератором.", show_alert=True)
                try: bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None) 
                except: pass
                return

            bot.answer_callback_query(call.id, "⏳ Одобряем и публикуем...")

            # Отправляем в канал
            try:
                if post["type"] in ["text", "photo", "video"]:
                    bot.copy_message(CHANNEL_ID, post["chat_id"], post["message_id"])
                elif post["type"] == "album":
                    bot.send_media_group(CHANNEL_ID, post["media"])
            except Exception as e:
                bot.send_message(chat_id, f"❌ Ошибка публикации: {e}")
                return

            # Уведомляем участника и модеров
            try: bot.send_message(post["user_id"], "✅ Ваше объявление успешно опубликовано!")
            except: pass
            
            notify_mods(f"✅ Модератор @{mod_name} одобрил объявление.")
            
            # Убираем кнопки, чтобы другие модеры не тыкали
            try: bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
            except: pass
            
            pending_posts.pop(post_id, None)

        elif data_cb.startswith("reject_"):
            post_id = data_cb.split("_")[1]
            
            if post_id not in pending_posts:
                bot.answer_callback_query(call.id, "❌ Заявка уже обработана или устарела.", show_alert=True)
                try: bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                except: pass
                return
                
            waiting_for_reject[call.from_user.id] = post_id
            bot.answer_callback_query(call.id)
            
            # Убираем кнопки сразу, чтобы показать, что процесс отказа запущен
            try: bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
            except: pass
            
            bot.send_message(chat_id, "✍️ Напишите причину отказа в чат (одним сообщением):")

        elif data_cb.startswith("msg_"):
            post_id = data_cb.split("_")[1]
            
            if post_id not in pending_posts:
                bot.answer_callback_query(call.id, "❌ Заявка уже обработана или устарела.", show_alert=True)
                try: bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                except: pass
                return
                
            waiting_for_msg[call.from_user.id] = post_id
            bot.answer_callback_query(call.id)
            bot.send_message(chat_id, "✍️ Напишите сообщение участнику в чат:")
            
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Произошла ошибка системы.", show_alert=False)
        print(f"Callback Error: {e}")

# 👑 КОМАНДЫ
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

@bot.message_handler(commands=['setadmin'])
def setadmin(message):
    if message.from_user.id != SUPERADMIN:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ Ошибка. Используйте: /setadmin @username")
        return
    username = args[1].replace("@", "").lower()
    if username not in usernames:
        bot.send_message(message.chat.id, "❌ Пользователь не найден (он должен запустить бота).")
        return
    uid = usernames[username]
    MODS.add(uid)
    data["mods"] = list(MODS)
    save_data()
    bot.send_message(message.chat.id, f"✅ @{username} теперь модератор")
    try: bot.send_message(uid, "🎉 Вы теперь модератор\nИспользуйте /help для списка команд.")
    except: pass

@bot.message_handler(commands=['deladmin'])
def deladmin(message):
    if message.from_user.id != SUPERADMIN:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ Ошибка. Используйте: /deladmin @username")
        return
    username = args[1].replace("@", "").lower()
    if username in usernames:
        uid = usernames[username]
        MODS.discard(uid)
        data["mods"] = list(MODS)
        save_data()
        try: bot.send_message(uid, "❌ Вы сняты с должности модератора.")
        except: pass
        bot.send_message(message.chat.id, "✅ Успешно сняли с должности")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id not in MODS:
        return
    bot.send_message(
        message.chat.id,
        "🛠 **Панель модератора:**\n"
        "/id @user — узнать ID\n"
        "/mute @user время(мин) причина\n"
        "/unmute @user — снять мут\n"
        "/ban @user — выдать бан\n"
        "/unban @user — снять бан\n"
        "/nlist — список модераторов\n"
        "/all текст — рассылка (только создатель)\n\n"
        "💬 *Если вы напишете обычный текст (не команду), он отправится в чат модераторов.*",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['id'])
def get_id(message):
    if message.from_user.id not in MODS: return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ Используйте: /id @username")
        return
    username = args[1].replace("@", "").lower()
    if username in usernames:
        bot.send_message(message.chat.id, f"🆔 ID пользователя: `{usernames[username]}`", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")

@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if message.from_user.id not in MODS: return
    args = message.text.split()
    if len(args) < 3:
        bot.send_message(message.chat.id, "❗ Ошибка. Используйте: /mute @username время(мин) причина")
        return
    username = args[1].replace("@", "").lower()
    try:
        minutes = int(args[2])
    except ValueError:
        bot.send_message(message.chat.id, "❗ Время должно быть числом (минуты).")
        return
    reason = " ".join(args[3:]) if len(args) > 3 else "Без причины"

    if username in usernames:
        uid = usernames[username]
        mutes[uid] = time.time() + minutes * 60
        try: bot.send_message(uid, f"⛔ Вам выдан мут на {minutes} мин.\nПричина: {reason}")
        except: pass
        bot.send_message(message.chat.id, f"✅ @{username} замучен.")

@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if message.from_user.id not in MODS: return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ Ошибка. Используйте: /ban @username")
        return
    username = args[1].replace("@", "").lower()
    if username in usernames:
        uid = usernames[username]
        bans[uid] = True
        try: bot.send_message(uid, "⛔ Вы забанены навсегда.")
        except: pass
        bot.send_message(message.chat.id, f"✅ @{username} забанен.")

@bot.message_handler(commands=['all'])
def all_cmd(message):
    if message.from_user.id != SUPERADMIN: return
    text = message.text.replace("/all", "").strip()
    if not text:
        bot.send_message(message.chat.id, "❗ Ошибка. Напишите текст для рассылки. Пример: /all Привет!")
        return
    count = 0
    for uid in users:
        try:
            bot.send_message(int(uid), text)
            count += 1
        except: pass
    bot.send_message(message.chat.id, f"✅ Рассылка завершена. Отправлено: {count} чел.")

@bot.message_handler(commands=['unmute'])
def unmute_cmd(message):
    if message.from_user.id not in MODS: return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ Ошибка. Используйте: /unmute @username")
        return
    username = args[1].replace("@", "").lower()
    if username in usernames:
        uid = usernames[username]
        mutes.pop(uid, None)
        try: bot.send_message(uid, "🔓 Ваш мут был снят.")
        except: pass
        bot.send_message(message.chat.id, f"✅ Мут снят с @{username}.")

@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if message.from_user.id not in MODS: return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❗ Ошибка. Используйте: /unban @username")
        return
    username = args[1].replace("@", "").lower()
    if username in usernames:
        uid = usernames[username]
        bans.pop(uid, None)
        try: bot.send_message(uid, "🔓 Ваш бан был снят.")
        except: pass
        bot.send_message(message.chat.id, f"✅ Бан снят с @{username}.")

@bot.message_handler(commands=['nlist'])
def nlist(message):
    if message.from_user.id not in MODS: return
    text = "👮‍♂️ Список модераторов:\n\n"
    for i, mod_id in enumerate(MODS, 1):
        uname = None
        for u, uid in usernames.items():
            if uid == mod_id:
                uname = u
                break
        if uname: text += f"{i}. @{uname} | ID: {mod_id}\n"
        else: text += f"{i}. ID: {mod_id}\n"
    bot.send_message(message.chat.id, text)

# 🔥 ПЕРЕХВАТ НЕИЗВЕСТНЫХ КОМАНД
@bot.message_handler(func=lambda message: message.text and message.text.startswith('/'))
def unknown_command(message):
    bot.send_message(message.chat.id, "❌ Данной команды не существует или она вам недоступна.")

# 📩 ОБРАБОТКА ТЕКСТА, ФОТО И АЛЬБОМОВ
@bot.message_handler(content_types=['text', 'photo', 'video'])
def all_messages(message):
    uid = message.from_user.id
    mod_name = message.from_user.username or message.from_user.first_name

    # 1. Стейт: Ожидание причины ОТКАЗА
    if uid in waiting_for_reject:
        post_id = waiting_for_reject[uid]
        reason = message.text or "Без причины"
        post = pending_posts.get(post_id)
        
        if post:
            try: bot.send_message(post["user_id"], f"❌ **Ваше объявление отклонено!**\n📋 Причина: {reason}", parse_mode="Markdown")
            except: pass
            
            notify_mods(f"❌ Модератор @{mod_name} отклонил объявление.\n📋 Причина: {reason}")
            pending_posts.pop(post_id, None)
            
        del waiting_for_reject[uid]
        bot.send_message(message.chat.id, "✅ Отказ и причина отправлены участнику.")
        return

    # 2. Стейт: Ожидание СООБЩЕНИЯ участнику
    if uid in waiting_for_msg:
        post_id = waiting_for_msg[uid]
        text_to_user = message.text or "Без текста"
        post = pending_posts.get(post_id)
        
        if post:
            try:
                bot.send_message(post["user_id"], f"💬 **Сообщение от модератора:**\n{text_to_user}", parse_mode="Markdown")
                bot.send_message(message.chat.id, "✅ Сообщение успешно отправлено участнику.")
            except: 
                bot.send_message(message.chat.id, "❌ Ошибка: Участник заблокировал бота.")
        del waiting_for_msg[uid]
        return

    # 3. Внутренний ЧАТ модераторов
    if uid in MODS:
        for m in MODS:
            if m != uid:
                text_to_send = f"👮‍♂️ **Модератор @{mod_name}:**\n{message.text or '[Медиафайл]'}"
                try: bot.send_message(m, text_to_send, parse_mode="Markdown")
                except: pass
        return 

    # --- ЛОГИКА ПОДАЧИ ОБЪЯВЛЕНИЙ ДЛЯ УЧАСТНИКОВ ---
    register_user(message)

    if uid in bans: return
    if uid in mutes and time.time() < mutes[uid]:
        bot.send_message(uid, "🔇 У вас мут. Вы не можете подавать объявления.")
        return

    post_id = str(int(time.time() * 1000))

    # 🔥 Обработка АЛЬБОМОВ (Media Group)
    if message.media_group_id:
        gid = message.media_group_id

        if gid not in media_groups:
            media_groups[gid] = [message]
            msg_alert = bot.send_message(uid, "⏳ Альбом загружается, ожидайте...")
            time.sleep(2) 
            
            msgs = media_groups.pop(gid, None)
            if not msgs: return

            first_caption = msgs[0].caption or ""
            if "@" not in first_caption:
                bot.send_message(uid, "❌ Добавьте ваш @username в описание альбома и отправьте заново.")
                return

            bot.edit_message_text("⏳ Альбом загружен. Ожидайте проверки модераторами.", chat_id=uid, message_id=msg_alert.message_id)

            media_to_send = []
            for i, m in enumerate(msgs):
                cap = m.caption if i == 0 else "" 
                if m.photo:
                    media_to_send.append(types.InputMediaPhoto(m.photo[-1].file_id, caption=cap))
                elif m.video:
                    media_to_send.append(types.InputMediaVideo(m.video.file_id, caption=cap))

            pending_posts[post_id] = {
                "type": "album",
                "media": media_to_send,
                "user_id": uid,
                "chat_id": message.chat.id
            }

            for m in MODS:
                try:
                    bot.send_media_group(m, media_to_send)
                    bot.send_message(m, f"📢 Новое объявление (Альбом) от ID: `{uid}`\nВыберите действие:", reply_markup=mod_kb(post_id), parse_mode="Markdown")
                except: pass
        else:
            media_groups[gid].append(message)
        return

    # Обработка ОДИНОЧНЫХ сообщений
    text_or_caption = message.text or message.caption or ""
    if "@" not in text_or_caption:
        bot.send_message(uid, "❌ Добавьте ваш @username в текст и отправьте заново.")
        return

    bot.send_message(uid, "⏳ Ожидайте проверки модераторами.")

    pending_posts[post_id] = {
        "type": "photo" if message.photo else ("video" if message.video else "text"),
        "user_id": uid,
        "chat_id": message.chat.id,
        "message_id": message.message_id
    }

    for m in MODS:
        try:
            bot.copy_message(m, message.chat.id, message.message_id)
            bot.send_message(m, f"📢 Новое объявление от ID: `{uid}`\nВыберите действие:", reply_markup=mod_kb(post_id), parse_mode="Markdown")
        except: pass

bot.infinity_polling(skip_pending=True)
