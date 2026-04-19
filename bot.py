import telebot
import time
import json
import os
from telebot import types

TOKEN = "8454142474:AAFPX2iAa9FEIAHfLndTbR1h79NZepDJdDs"
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857
DATA_FILE = "data.json"
CHANNEL_ID = "@br_bu_astana"

# 🔥 СТРУКТУРЫ ДАННЫХ
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"mods": [SUPERADMIN], "users": {}, "usernames": {}, "bans": [], "mutes": {}}
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
        return {"mods": [SUPERADMIN], "users": {}, "usernames": {}, "bans": [], "mutes": {}}

def save_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                old = f.read()
            with open("data_backup.json", "w", encoding="utf-8") as f:
                f.write(old)
                
        data["mods"] = list(MODS)
        data["bans"] = list(bans)
        data["mutes"] = mutes
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("Ошибка сохранения:", e)

data = load_data()

# Инициализация структур
if "mods" not in data: data["mods"] = [SUPERADMIN]
if "users" not in data: data["users"] = {}
if "usernames" not in data: data["usernames"] = {}
if "bans" not in data: data["bans"] = []
if "mutes" not in data: data["mutes"] = {}

MODS = set(data["mods"])
users = data["users"]
usernames = data["usernames"]
bans = set(data["bans"])
mutes = data["mutes"]

# Временные хранилища
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
    all_admins = MODS.union({SUPERADMIN})
    for m in all_admins:
        try:
            bot.send_message(m, text, parse_mode="Markdown")
        except:
            pass

def get_user_id(username_str):
    uname = username_str.replace("@", "").lower()
    return str(usernames.get(uname)) if uname in usernames else None

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

# 🔥 CALLBACK (Кнопки модерации)
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        data_cb = call.data
        mod_name = call.from_user.username or call.from_user.first_name

        if data_cb.startswith("approve_"):
            post_id = data_cb.split("_")[1]
            post = pending_posts.get(post_id)

            if not post:
                bot.answer_callback_query(call.id, "❌ Ошибка: Пост устарел, удален или бот был перезапущен!", show_alert=True)
                return

            bot.answer_callback_query(call.id, "✅ Публикуем...")

            try:
                if post["type"] in ["text", "photo", "video"]:
                    bot.copy_message(CHANNEL_ID, post["chat_id"], post["message_id"])
                elif post["type"] == "album":
                    bot.send_media_group(CHANNEL_ID, post["media"])

                try: bot.send_message(post["user_id"], "✅ Ваше объявление успешно опубликовано!")
                except: pass
                
                notify_mods(f"✅ Модератор @{mod_name} **одобрил** объявление.")
                
                try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                except: pass
                
                pending_posts.pop(post_id, None)

            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ **Ошибка при отправке в канал!**\nПроверь права бота.\nКод ошибки: `{e}`", parse_mode="Markdown")

        elif data_cb.startswith("reject_"):
            post_id = data_cb.split("_")[1]
            if post_id not in pending_posts:
                bot.answer_callback_query(call.id, "❌ Пост уже обработан.", show_alert=True)
                return
                
            waiting_for_reject[call.from_user.id] = post_id
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "✍️ Напишите причину отказа в чат (одним сообщением):")

        elif data_cb.startswith("msg_"):
            post_id = data_cb.split("_")[1]
            if post_id not in pending_posts:
                bot.answer_callback_query(call.id, "❌ Пост уже обработан.", show_alert=True)
                return
                
            waiting_for_msg[call.from_user.id] = post_id
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "✍️ Напишите сообщение участнику в чат:")

    except Exception as e:
        bot.answer_callback_query(call.id, "⚠️ Системная ошибка!", show_alert=True)
        bot.send_message(call.message.chat.id, f"⚠️ Ошибка: {e}")

# 👑 КОМАНДЫ ПОЛЬЗОВАТЕЛЕЙ
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

# 🛠 ПАНЕЛЬ УПРАВЛЕНИЯ (HELP)
@bot.message_handler(commands=['help'])
def help_cmd(message):
    uid = message.from_user.id
    if uid not in MODS and uid != SUPERADMIN: 
        return

    text = "🛠 **Панель модератора:**\n"
    text += "🔹 `/id @user` — узнать ID участника\n"
    text += "🔹 `/mute @user время(в минутах) причина` — выдать мут\n"
    text += "🔹 `/unmute @user` — снять мут\n"
    text += "🔹 `/ban @user` — выдать бан (навсегда)\n"
    text += "🔹 `/unban @user` — снять бан\n"
    text += "🔹 `/nlist` — список модераторов\n\n"
    text += "💬 *Напишите обычный текст, фото или видео, чтобы отправить его в чат модераторов.*\n"

    if uid == SUPERADMIN:
        text += "\n👑 **Команды Создателя:**\n"
        text += "🔸 `/setadmin @user` — назначить модератора\n"
        text += "🔸 `/deladmin @user` — снять модератора\n"
        text += "🔸 `/all текст` — рассылка всем участникам\n"
        text += "🔸 `/stats` — статистика бота\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# 👮 КОМАНДЫ МОДЕРАТОРОВ
@bot.message_handler(commands=['id'])
def get_id(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    if len(args) < 2:
        return bot.send_message(message.chat.id, "❌ Формат: `/id @user`", parse_mode="Markdown")
    
    target_id = get_user_id(args[1])
    if target_id: bot.send_message(message.chat.id, f"🔍 ID пользователя {args[1]}: `{target_id}`", parse_mode="Markdown")
    else: bot.send_message(message.chat.id, "❌ Пользователь не найден. Возможно, он не запускал бота.")

@bot.message_handler(commands=['mute'])
def mute_user(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    args = message.text.split(maxsplit=3)
    if len(args) < 3:
        return bot.send_message(message.chat.id, "❌ Формат: `/mute @user время_в_минутах причина`", parse_mode="Markdown")
    
    target_id = get_user_id(args[1])
    if not target_id: return bot.send_message(message.chat.id, "❌ Пользователь не найден.")
    
    try:
        minutes = int(args[2])
        reason = args[3] if len(args) > 3 else "Без причины"
        mutes[target_id] = time.time() + (minutes * 60)
        save_data()
        bot.send_message(message.chat.id, f"✅ Пользователь {args[1]} получил мут на {minutes} мин.\n📋 Причина: {reason}")
        try: bot.send_message(int(target_id), f"🔇 Вы получили мут на {minutes} минут.\n📋 Причина: {reason}")
        except: pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка: Время должно быть числом.")

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Формат: `/unmute @user`", parse_mode="Markdown")
    
    target_id = get_user_id(args[1])
    if target_id in mutes:
        del mutes[target_id]
        save_data()
        bot.send_message(message.chat.id, f"✅ Мут с пользователя {args[1]} снят.")
        try: bot.send_message(int(target_id), "🔊 Ваш мут снят. Вы можете подавать объявления.")
        except: pass
    else: bot.send_message(message.chat.id, "❌ У этого пользователя нет мута.")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Формат: `/ban @user`", parse_mode="Markdown")
    
    target_id = get_user_id(args[1])
    if not target_id: return bot.send_message(message.chat.id, "❌ Пользователь не найден.")
    
    bans.add(target_id)
    save_data()
    bot.send_message(message.chat.id, f"✅ Пользователь {args[1]} забанен.")
    try: bot.send_message(int(target_id), "🚫 Вы получили блокировку в боте.")
    except: pass

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Формат: `/unban @user`", parse_mode="Markdown")
    
    target_id = get_user_id(args[1])
    if target_id in bans:
        bans.remove(target_id)
        save_data()
        bot.send_message(message.chat.id, f"✅ Пользователь {args[1]} разбанен.")
        try: bot.send_message(int(target_id), "✅ Ваш бан снят. Добро пожаловать обратно!")
        except: pass
    else: bot.send_message(message.chat.id, "❌ Этот пользователь не в бане.")

@bot.message_handler(commands=['nlist'])
def nlist(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    text = "👮‍♂️ **Список модераторов:**\n\n"
    
    # Создаем обратный словарь для поиска @username по ID
    id_to_name = {v: k for k, v in usernames.items()}
    
    for i, mod_id in enumerate(MODS, 1):
        uname = id_to_name.get(mod_id)
        if uname:
            text += f"{i}. @{uname}\n"
        else:
            text += f"{i}. ID: `{mod_id}`\n"
            
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# 👑 КОМАНДЫ ВЛАДЕЛЬЦА
@bot.message_handler(commands=['setadmin'])
def setadmin(message):
    if message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Формат: `/setadmin @user`", parse_mode="Markdown")
    
    uid = get_user_id(args[1])
    if not uid: return bot.send_message(message.chat.id, "❌ Пользователь не найден. Он должен хотя бы раз запустить бота.")
    
    MODS.add(int(uid))
    save_data()
    bot.send_message(message.chat.id, f"✅ Пользователь {args[1]} назначен модератором.")
    try: 
        bot.send_message(int(uid), "🎉 **Поздравляем!** 🎉\nВам были выданы права **Модератора**! 👮‍♂️\n\n📌 Ознакомьтесь с доступными командами управления, написав команду: /help", parse_mode="Markdown")
    except: pass

@bot.message_handler(commands=['deladmin'])
def deladmin(message):
    if message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Формат: `/deladmin @user`", parse_mode="Markdown")
    
    uid = get_user_id(args[1])
    if uid and int(uid) in MODS:
        MODS.discard(int(uid))
        save_data()
        bot.send_message(message.chat.id, f"✅ {args[1]} снят с должности модератора.")
        try: 
            bot.send_message(int(uid), "😔 **Внимание!**\nВы были сняты с должности модератора.", parse_mode="Markdown")
        except: pass
    else: bot.send_message(message.chat.id, "❌ Этот пользователь не является модератором.")

@bot.message_handler(commands=['all'])
def broadcast(message):
    if message.from_user.id != SUPERADMIN: return
    text = message.text.replace("/all", "").strip()
    if not text:
        return bot.send_message(message.chat.id, "❌ Введите текст для рассылки.\nПример: `/all Внимание, важная новость!`", parse_mode="Markdown")
    
    bot.send_message(message.chat.id, "⏳ Начинаю рассылку... Это может занять время.")
    count = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 **Объявление от администрации:**\n\n{text}", parse_mode="Markdown")
            count += 1
        except: pass
        
    bot.send_message(message.chat.id, f"✅ **Рассылка завершена!**\nСообщение успешно получили: **{count}** чел.", parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != SUPERADMIN: return
    text = f"📊 **Статистика бота:**\n\n"
    text += f"👥 Всего пользователей: **{len(users)}**\n"
    text += f"👮‍♂️ Модераторов: **{len(MODS)}**\n"
    text += f"🚫 В бане: **{len(bans)}**\n"
    text += f"🔇 В муте сейчас: **{len([m for m, t in mutes.items() if t > time.time()])}**\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# 🔥 ПЕРЕХВАТ НЕИЗВЕСТНЫХ КОМАНД
@bot.message_handler(func=lambda message: message.text and message.text.startswith('/'))
def unknown_command(message):
    bot.send_message(message.chat.id, "❌ Данной команды не существует или она вам недоступна.")

# 📩 ОБРАБОТКА ТЕКСТА, ФОТО, ВИДЕО И ДР. МЕДИА
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'voice', 'audio'])
def all_messages(message):
    uid = message.from_user.id
    uid_str = str(uid)
    mod_name = message.from_user.username or message.from_user.first_name

    # 1. Стейт: Ожидание причины ОТКАЗА
    if uid in waiting_for_reject:
        post_id = waiting_for_reject[uid]
        reason = message.text or "Без причины"
        post = pending_posts.get(post_id)
        
        if post:
            try: bot.send_message(post["user_id"], f"❌ **Ваше объявление отклонено!**\n📋 Причина: {reason}", parse_mode="Markdown")
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
            except: bot.send_message(message.chat.id, "❌ Ошибка: Участник заблокировал бота.")
        del waiting_for_msg[uid]
        return

    # 3. Внутренний ЧАТ модераторов
    if uid in MODS or uid == SUPERADMIN:
        all_admins = MODS.union({SUPERADMIN})
        for m in all_admins:
            if m != uid:
                try:
                    if message.text:
                        bot.send_message(m, f"💬 **Модератор @{mod_name}:**\n{message.text}", parse_mode="Markdown")
                    else:
                        bot.send_message(m, f"🖼 **Модератор @{mod_name} отправил файл:**", parse_mode="Markdown")
                        bot.copy_message(m, message.chat.id, message.message_id)
                except: pass
        # Модераторы не могут подавать заявки как юзеры (все их сообщения идут в чат)
        return

    # --- ЛОГИКА ПОДАЧИ ОБЪЯВЛЕНИЙ ДЛЯ УЧАСТНИКОВ ---
    register_user(message)

    if uid_str in bans: 
        return
        
    if uid_str in mutes:
        if time.time() < mutes[uid_str]:
            left_mins = int((mutes[uid_str] - time.time()) / 60)
            bot.send_message(uid, f"🔇 У вас мут. Вы не можете подавать объявления.\n⏳ Осталось: {left_mins} мин.")
            return
        else:
            del mutes[uid_str] # Мут истек
            save_data()

    post_id = str(int(time.time() * 1000))

    if message.media_group_id:
        gid = message.media_group_id
        if gid not in media_groups:
            media_groups[gid] = [message]
            bot.send_message(uid, "⏳ Альбом загружается, ожидайте проверки...")
            time.sleep(2) 
            msgs = media_groups.pop(gid, None)
            if not msgs: return

            first_caption = msgs[0].caption or ""
            if "@" not in first_caption:
                bot.send_message(uid, "❌ Добавьте ваш @username в описание альбома и отправьте заново.")
                return

            media_to_send = []
            for i, m in enumerate(msgs):
                cap = m.caption if i == 0 else ""
                if m.photo: media_to_send.append(types.InputMediaPhoto(m.photo[-1].file_id, caption=cap))
                elif m.video: media_to_send.append(types.InputMediaVideo(m.video.file_id, caption=cap))

            pending_posts[post_id] = {"type": "album", "media": media_to_send, "user_id": uid, "chat_id": message.chat.id}

            for m in MODS.union({SUPERADMIN}):
                try:
                    bot.send_media_group(m, media_to_send)
                    bot.send_message(m, f"📢 **Новое объявление (Альбом)** от ID: `{uid}`\nВыберите действие:", reply_markup=mod_kb(post_id), parse_mode="Markdown")
                except: pass
        else:
            media_groups[gid].append(message)
        return

    text_or_caption = message.text or message.caption or ""
    if "@" not in text_or_caption:
        bot.send_message(uid, "❌ Добавьте ваш @username в текст и отправьте заново.")
        return

    bot.send_message(uid, "⏳ Объявление отправлено! Ожидайте проверки модераторами.")

    pending_posts[post_id] = {
        "type": "photo" if message.photo else ("video" if message.video else "text"),
        "user_id": uid,
        "chat_id": message.chat.id,
        "message_id": message.message_id
    }

    for m in MODS.union({SUPERADMIN}):
        try:
            bot.copy_message(m, message.chat.id, message.message_id)
            bot.send_message(m, f"📢 **Новое объявление** от ID: `{uid}`\nВыберите действие:", reply_markup=mod_kb(post_id), parse_mode="Markdown")
        except: pass

bot.infinity_polling(skip_pending=True)
