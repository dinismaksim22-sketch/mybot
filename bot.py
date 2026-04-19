import telebot
import time
import json
import os
from telebot import types

# --- НАСТРОЙКИ ---
TOKEN = "8454142474:AAFPX2iAa9FEIAHfLndTbR1h79NZepDJdDs"
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857
DATA_FILE = "data.json"
CHANNEL_ID = "@br_bu_astana"

# 🔥 РАБОТА С ДАННЫМИ
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"mods": [SUPERADMIN], "users": {}, "usernames": {}, "bans": [], "mutes": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Ошибка чтения базы: {e}")
        return {"mods": [SUPERADMIN], "users": {}, "usernames": {}, "bans": [], "mutes": {}}

def save_data():
    try:
        # Резервная копия
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                backup = f.read()
            with open("data_backup.json", "w", encoding="utf-8") as f:
                f.write(backup)
                
        data["mods"] = list(MODS)
        data["bans"] = list(bans)
        data["mutes"] = mutes
        data["users"] = users
        data["usernames"] = usernames
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

data = load_data()

# Инициализация структур
MODS = set(data.get("mods", [SUPERADMIN]))
users = data.get("users", {})
usernames = data.get("usernames", {}) # Здесь хранится {"username": id}
bans = set(data.get("bans", []))
mutes = data.get("mutes", {})

# Временные переменные
media_groups = {}
pending_posts = {}
waiting_for_reject = {} 
waiting_for_msg = {}    
waiting_for_broadcast = set() 

def register_user(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    if user_id not in users:
        users[user_id] = {"count": 0}
    if username:
        # Сохраняем и маленькими буквами для поиска, и ID как значение
        usernames[username.lower()] = int(user_id)
    save_data()

def get_user_id(username_str):
    uname = username_str.replace("@", "").lower()
    return str(usernames.get(uname)) if uname in usernames else None

# 🔥 КНОПКИ МОДЕРАЦИИ
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

# 🔥 ОБРАБОТКА КНОПОК
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    mod_id = call.from_user.id
    if mod_id not in MODS and mod_id != SUPERADMIN:
        return bot.answer_callback_query(call.id, "Доступ закрыт!")

    data_cb = call.data
    mod_name = call.from_user.username or call.from_user.first_name

    if data_cb.startswith("approve_"):
        post_id = data_cb.split("_")[1]
        post = pending_posts.get(post_id)
        if not post:
            return bot.answer_callback_query(call.id, "Пост не найден!", show_alert=True)

        try:
            if post["type"] in ["text", "photo", "video"]:
                bot.copy_message(CHANNEL_ID, post["chat_id"], post["message_id"])
            elif post["type"] == "album":
                bot.send_media_group(CHANNEL_ID, post["media"])

            bot.send_message(post["user_id"], "✅ Ваше объявление успешно опубликовано!")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            pending_posts.pop(post_id, None)
            bot.answer_callback_query(call.id, "Опубликовано")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"Ошибка: {e}")

    elif data_cb.startswith("reject_"):
        waiting_for_reject[mod_id] = data_cb.split("_")[1]
        bot.send_message(call.message.chat.id, "✍️ Введите причину отказа:")
        bot.answer_callback_query(call.id)

    elif data_cb.startswith("msg_"):
        waiting_for_msg[mod_id] = data_cb.split("_")[1]
        bot.send_message(call.message.chat.id, "✍️ Введите сообщение для юзера:")
        bot.answer_callback_query(call.id)

# 👑 КОМАНДА /START
@bot.message_handler(commands=['start'])
def start_cmd(message):
    register_user(message)
    text = (
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
    bot.send_message(message.chat.id, text)

# 🛠 ПАНЕЛЬ ПОМОЩИ
@bot.message_handler(commands=['help'])
def help_cmd(message):
    uid = message.from_user.id
    if uid not in MODS and uid != SUPERADMIN: return
    
    text = "🛠 **Панель модератора:**\n"
    text += "🔹 `/id @user` — узнать ID\n"
    text += "🔹 `/mute @user время причина`\n"
    text += "🔹 `/unmute @user`\n"
    text += "🔹 `/ban @user`\n"
    text += "🔹 `/unban @user`\n"
    text += "🔹 `/nlist` — список модераторов\n"
    
    if uid == SUPERADMIN:
        text += "\n👑 **Команды Создателя:**\n"
        text += "🔸 `/setadmin @user` — назначить модератора\n"
        text += "🔸 `/deladmin @user` — снять модератора\n"
        text += "🔸 `/all` — рассылка\n"
        text += "🔸 `/stats` — статистика\n"
        
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# 👮 УПРАВЛЕНИЕ АДМИНАМИ
@bot.message_handler(commands=['setadmin'])
def set_admin(message):
    if message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "Укажите @username")
    
    uid = get_user_id(args[1])
    if uid:
        MODS.add(int(uid))
        save_data()
        bot.send_message(message.chat.id, f"✅ {args[1]} теперь модератор.")
        # УВЕДОМЛЕНИЕ ДЛЯ НОВОГО МОДЕРА
        try:
            bot.send_message(int(uid), "🎉 Поздравляем! 🎉\nВам были выданы права Модератора! 👮‍♂️\n\n📌 Ознакомьтесь с доступными командами управления, написав команду: /help")
        except: pass
    else:
        bot.send_message(message.chat.id, "Юзер не найден в базе.")

@bot.message_handler(commands=['deladmin'])
def del_admin(message):
    if message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    if len(args) < 2: return
    
    uid = get_user_id(args[1])
    if uid and int(uid) in MODS:
        MODS.discard(int(uid))
        save_data()
        bot.send_message(message.chat.id, f"❌ {args[1]} больше не модератор.")
        # УВЕДОМЛЕНИЕ О СНЯТИИ
        try:
            bot.send_message(int(uid), "😔 Внимание!\nВы были сняты с должности модератора.")
        except: pass

# 👮 КОМАНДА /NLIST (ИСПРАВЛЕНО)
@bot.message_handler(commands=['nlist'])
def nlist_cmd(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    
    text = "👮‍♂️ **Список модераторов:**\n\n"
    # Создаем карту ID -> Username
    id_to_name = {val: key for key, val in usernames.items()}
    
    all_mods = sorted(list(MODS))
    for i, m_id in enumerate(all_mods, 1):
        uname = id_to_name.get(m_id)
        if uname:
            text += f"{i}. @{uname}\n"
        else:
            text += f"{i}. ID: `{m_id}` (юза нет в базе)\n"
            
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# 👮 ОСТАЛЬНЫЕ КОМАНДЫ
@bot.message_handler(commands=['id'])
def id_cmd(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    if len(args) < 2: return
    tid = get_user_id(args[1])
    if tid: bot.send_message(message.chat.id, f"ID {args[1]}: `{tid}`", parse_mode="Markdown")

@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    args = message.text.split(maxsplit=3)
    if len(args) < 3: return
    tid = get_user_id(args[1])
    if tid:
        mutes[tid] = time.time() + (int(args[2]) * 60)
        save_data()
        bot.send_message(message.chat.id, f"✅ Мут {args[1]} на {args[2]} мин.")

@bot.message_handler(commands=['unmute'])
def unmute_cmd(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    tid = get_user_id(args[1])
    if tid in mutes:
        del mutes[tid]
        save_data()
        bot.send_message(message.chat.id, "Снят.")

@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    tid = get_user_id(args[1])
    if tid:
        bans.add(tid)
        save_data()
        bot.send_message(message.chat.id, "Бан.")

@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN: return
    args = message.text.split()
    tid = get_user_id(args[1])
    if tid in bans:
        bans.remove(tid)
        save_data()
        bot.send_message(message.chat.id, "Разбан.")

@bot.message_handler(commands=['all'])
def all_broadcast(message):
    if message.from_user.id != SUPERADMIN: return
    waiting_for_broadcast.add(message.from_user.id)
    bot.send_message(message.chat.id, "📢 Отправьте сообщение для рассылки:")

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.from_user.id != SUPERADMIN: return
    bot.send_message(message.chat.id, f"Юзеров: {len(users)}\nМодов: {len(MODS)}\nБаны: {len(bans)}")

# 🔥 ОСНОВНОЙ ОБРАБОТЧИК
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'voice', 'audio'])
def handle_messages(message):
    uid = message.from_user.id
    uid_str = str(uid)
    u_tag = message.from_user.username or f"ID{uid}"

    # Рассылка
    if uid == SUPERADMIN and uid in waiting_for_broadcast:
        waiting_for_broadcast.remove(uid)
        for target in users:
            try: bot.copy_message(int(target), message.chat.id, message.message_id)
            except: pass
        bot.send_message(uid, "Рассылка готова.")
        return

    # Причина отказа
    if uid in waiting_for_reject:
        pid = waiting_for_reject.pop(uid)
        post = pending_posts.get(pid)
        if post:
            bot.send_message(post["user_id"], f"❌ Отклонено. Причина: {message.text}")
            pending_posts.pop(pid, None)
        return

    # Сообщение юзеру
    if uid in waiting_for_msg:
        pid = waiting_for_msg.pop(uid)
        post = pending_posts.get(pid)
        if post:
            bot.send_message(post["user_id"], f"💬 Сообщение от администрации:\n{message.text}")
        return

    # 🛡 ЧАТ МОДЕРАТОРОВ (ИСПРАВЛЕНО - ОДНО СООБЩЕНИЕ)
    if uid in MODS or uid == SUPERADMIN:
        header = f"🛡 Модератор @{u_tag}:\n"
        all_admins = MODS.union({SUPERADMIN})
        for admin in all_admins:
            if admin != uid:
                try:
                    if message.text:
                        bot.send_message(admin, header + message.text)
                    elif message.photo:
                        bot.send_photo(admin, message.photo[-1].file_id, caption=header + (message.caption or ""))
                    elif message.video:
                        bot.send_video(admin, message.video.file_id, caption=header + (message.caption or ""))
                    else:
                        # Для прочих файлов (доки, аудио)
                        bot.send_message(admin, header)
                        bot.copy_message(admin, message.chat.id, message.message_id)
                except: pass
        return

    # --- ПОДАЧА ОБЪЯВЛЕНИЙ ---
    register_user(message)
    if uid_str in bans: return
    if uid_str in mutes and time.time() < mutes[uid_str]:
        return bot.send_message(uid, "🔇 У вас мут.")

    content = message.text or message.caption or ""
    if "@" not in content:
        return bot.send_message(uid, "❌ Ошибка: Вы не указали @username в тексте!")

    # ТВОЙ ТЕКСТ ПОДТВЕРЖДЕНИЯ
    bot.send_message(uid, "⏳ Ожидайте, все объявления проверяются модераторами, не нужно дублировать сообщение.")

    post_id = str(int(time.time() * 1000))
    
    # Альбомы
    if message.media_group_id:
        gid = message.media_group_id
        if gid not in media_groups:
            media_groups[gid] = [message]
            time.sleep(2)
            msgs = media_groups.pop(gid, None)
            if not msgs: return
            album = []
            for i, m in enumerate(msgs):
                cap = m.caption if i == 0 else ""
                if m.photo: album.append(types.InputMediaPhoto(m.photo[-1].file_id, caption=cap))
                elif m.video: album.append(types.InputMediaVideo(m.video.file_id, caption=cap))
            pending_posts[post_id] = {"type": "album", "media": album, "user_id": uid, "chat_id": message.chat.id}
            for admin in MODS.union({SUPERADMIN}):
                try:
                    bot.send_media_group(admin, album)
                    bot.send_message(admin, f"📢 Альбом от ID: `{uid}`", reply_markup=mod_kb(post_id))
                except: pass
        else:
            media_groups[gid].append(message)
        return

    # Одиночное медиа/текст
    pending_posts[post_id] = {
        "type": "photo" if message.photo else ("video" if message.video else "text"),
        "user_id": uid, "chat_id": message.chat.id, "message_id": message.message_id
    }
    for admin in MODS.union({SUPERADMIN}):
        try:
            bot.copy_message(admin, message.chat.id, message.message_id)
            bot.send_message(admin, f"📢 Пост от ID: `{uid}`", reply_markup=mod_kb(post_id))
        except: pass

bot.infinity_polling(skip_pending=True)
