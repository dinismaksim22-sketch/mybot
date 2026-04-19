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

media_groups = {}
pending_posts = {}
waiting_for_reject = {}
waiting_for_msg = {}

def register_user(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    if user_id not in users:
        users[user_id] = {"count": 0}
    if username:
        usernames[username.lower()] = int(user_id)
    save_data()

def notify_mods(text):
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

# 🔥 CALLBACK (ИСПРАВЛЕН)
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        print("CALLBACK:", call.data)

        # 🔥 СРАЗУ СНИМАЕМ ЗАГРУЗКУ (ЭТО КРИТИЧНО)
        bot.answer_callback_query(call.id)

        data_cb = call.data
        mod_name = call.from_user.username or call.from_user.first_name

        if "_" not in data_cb:
            return

        action, post_id = data_cb.split("_", 1)

        post = pending_posts.get(post_id)

        # ---------------- APPROVE ----------------
        if action == "approve":

            if not post:
                bot.send_message(call.message.chat.id, "❌ Пост не найден")
                return

            if post["type"] in ["text", "photo", "video"]:
                bot.copy_message(CHANNEL_ID, post["chat_id"], post["message_id"])

            elif post["type"] == "album":
                bot.send_media_group(CHANNEL_ID, post["media"])

            try:
                bot.send_message(post["user_id"], "✅ Одобрено")
            except:
                pass

            notify_mods(f"✅ @{mod_name} одобрил объявление")

            pending_posts.pop(post_id, None)

            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )

        # ---------------- REJECT ----------------
        elif action == "reject":
            waiting_for_reject[call.from_user.id] = post_id
            bot.send_message(call.message.chat.id, "✍️ Напишите причину отказа:")

        # ---------------- MESSAGE ----------------
        elif action == "msg":
            waiting_for_msg[call.from_user.id] = post_id
            bot.send_message(call.message.chat.id, "✍️ Напишите сообщение пользователю:")

    except Exception as e:
        print("🔥 CALLBACK ERROR:", e)
        try:
            bot.answer_callback_query(call.id, "❌ ошибка")
        except:
            pass
            
# 👇👇👇 ДАЛЬШЕ ТВОЙ КОД БЕЗ ИЗМЕНЕНИЙ 👇👇👇

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
    bot.send_message(uid, "🎉 Вы теперь модератор\nИспользуйте /help для списка команд.")

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
        bot.send_message(uid, "❌ Вы сняты с должности модератора.")
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
        bot.send_message(uid, f"⛔ Вам выдан мут на {minutes} мин.\nПричина: {reason}")
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
        bot.send_message(uid, "⛔ Вы забанены навсегда.")
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
        bot.send_message(uid, "🔓 Ваш мут был снят.")
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
        bot.send_message(uid, "🔓 Ваш бан был снят.")
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


# ИСПРАВЛЕНИЕ: Функция для обработки альбомов в фоновом потоке
def process_album(gid, uid, chat_id):
    time.sleep(2) # Ждем пока придут все фото, не блокируя остального бота
    msgs = media_groups.pop(gid, None)
    if not msgs: return

    post_id = str(int(time.time() * 1000))
    first_caption = msgs[0].caption or ""
    
    if "@" not in first_caption:
        bot.send_message(uid, "❌ Добавьте ваш @username в описание альбома и отправьте заново.")
        return

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
        "chat_id": chat_id
    }

    for m in MODS:
        try:
            bot.send_media_group(m, media_to_send)
            bot.send_message(m, f"📢 **Новое объявление (Альбом)** от ID: {uid}\nВыберите действие:", reply_markup=mod_kb(post_id), parse_mode="Markdown")
        except: pass


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
            try:
                bot.send_message(post["user_id"], f"❌ **Ваше объявление отклонено!**\n📋 Причина: {reason}", parse_mode="Markdown")
            except: pass
            
            notify_mods(f"❌ Модератор @{mod_name} **отклонил** объявление.\n📋 Причина: {reason}")
            pending_posts.pop(post_id, None)
            
        del waiting_for_reject[uid]
        bot.send_message(message.chat.id, "✅ Отказ отправлен участнику.")
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
        if not message.media_group_id and not (message.text and message.text.startswith('/')):
            for m in MODS:
                if m != uid:
                    text_to_send = f"👮‍♂️ **Модератор @{mod_name}:**\n{message.text or '[Медиафайл]'}"
                    try:
                        bot.send_message(m, text_to_send, parse_mode="Markdown")
                    except: pass
            return

    # --- НИЖЕ ИДЕТ ЛОГИКА ПОДАЧИ ОБЪЯВЛЕНИЙ ДЛЯ УЧАСТНИКОВ ---
    register_user(message)

    if uid in bans: return
    if uid in mutes and time.time() < mutes[uid]:
        bot.send_message(uid, "🔇 У вас мут. Вы не можете подавать объявления.")
        return

    post_id = str(int(time.time() * 1000))

    # 🔥 Обработка АЛЬБОМОВ (Media Group) - ИСПРАВЛЕНО
    if message.media_group_id:
        gid = message.media_group_id

        if gid not in media_groups:
            media_groups[gid] = [message]
            bot.send_message(uid, "⏳ Альбом загружается, ожидайте проверки...")
            # Запускаем сборку альбома в отдельном потоке, чтобы не ломать кнопки!
            threading.Thread(target=process_album, args=(gid, uid, message.chat.id)).start()
        else:
            media_groups[gid].append(message)
        return

    # Обработка ОДИНОЧНЫХ сообщений (Текст/Одно фото/Одно видео)
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
            bot.send_message(m, f"📢 **Новое объявление** от ID: {uid}\nВыберите действие:", reply_markup=mod_kb(post_id), parse_mode="Markdown")
        except: pass

bot.infinity_polling(skip_pending=True)
