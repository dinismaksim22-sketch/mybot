import telebot  
import time  
import json  
import os  
from telebot import types  
  
# --- КОНФИГУРАЦИЯ ---  
TOKEN = "8454142474:AAE0Jc1Gcj72MYIanozXgrF0Re0M5Vqb7K0"  
bot = telebot.TeleBot(TOKEN)  
  
SUPERADMIN = 7905149857  
DATA_FILE = "data.json"  
CHANNEL_ID = "@br_bu_astana"  
  
# 🔥 СТРУКТУРЫ ДАННЫХ И ЛОГИКА ФАЙЛОВ  
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
        # Создаем бэкап перед сохранением  
        if os.path.exists(DATA_FILE):  
            with open(DATA_FILE, "r", encoding="utf-8") as f:  
                old_data_content = f.read()  
            with open("data_backup.json", "w", encoding="utf-8") as f:  
                f.write(old_data_content)  
                  
        data["mods"] = list(MODS)  
        data["bans"] = list(bans)  
        data["mutes"] = mutes  
        data["users"] = users  
        data["usernames"] = usernames  
          
        with open(DATA_FILE, "w", encoding="utf-8") as f:  
            json.dump(data, f, indent=4, ensure_ascii=False)  
    except Exception as e:  
        print("Ошибка сохранения данных в файл:", e)  
  
data = load_data()  
  
# Инициализация всех структур  
if "mods" not in data:   
    data["mods"] = [SUPERADMIN]  
if "users" not in data:   
    data["users"] = {}  
if "usernames" not in data:   
    data["usernames"] = {}  
if "bans" not in data:   
    data["bans"] = []  
if "mutes" not in data:   
    data["mutes"] = {}  
  
MODS = set(data["mods"])  
users = data["users"]  
usernames = data["usernames"]  
bans = set(data["bans"])  
mutes = data["mutes"]  
  
# Временные операционные хранилища  
media_groups = {}  
pending_posts = {}  
waiting_for_reject = {}   
waiting_for_msg = {}      
waiting_for_broadcast = set() # Для команды /all  
  
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
    if uname in usernames:  
        return str(usernames.get(uname))  
    return None  
  
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
  
        # Проверка прав (на случай если кто-то нажмет кнопку)  
        if mod_id not in MODS and mod_id != SUPERADMIN:  
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
  
                # Уведомляем пользователя  
                try:   
                    bot.send_message(post["user_id"], "✅ Ваше объявление успешно опубликовано!")  
                except:   
                    pass  
                  
                notify_mods(f"✅ Модератор @{mod_name} **одобрил** объявление.")  
                  
                # Убираем кнопки  
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
  
# 🔥 КОМАНДА /START (ОБНОВЛЕННЫЙ ТЕКСТ)
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
    if uid not in MODS and uid != SUPERADMIN:   
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
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:   
        return      
          
    args = message.text.split()  
    if len(args) < 2:  
        return bot.send_message(message.chat.id, "❌ Формат: `/id @user`", parse_mode="Markdown")  
      
    target_id = get_user_id(args[1])  
    if target_id:   
        bot.send_message(message.chat.id, f"🔍 ID пользователя {args[1]}: `{target_id}`", parse_mode="Markdown")  
    else:   
        bot.send_message(message.chat.id, "❌ Пользователь не найден в базе.")  
  
@bot.message_handler(commands=['mute'])  
def mute_command(message):  
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:   
        return  
          
    args = message.text.split(maxsplit=3)  
    if len(args) < 3:  
        return bot.send_message(message.chat.id, "❌ Формат: `/mute @user время_в_минутах причина`", parse_mode="Markdown")  
      
    target_id = get_user_id(args[1])  
    if not target_id:   
        return bot.send_message(message.chat.id, "❌ Пользователь не найден.")  
      
    try:  
        minutes = int(args[2])  
        reason = args[3] if len(args) > 3 else "Не указана"  
        mutes[target_id] = time.time() + (minutes * 60)  
        save_data()  
          
        bot.send_message(message.chat.id, f"✅ Пользователь {args[1]} замучен на {minutes} мин.\n📋 Причина: {reason}")  
        try:   
            bot.send_message(int(target_id), f"🔇 Вы получили мут на {minutes} минут.\n📋 Причина: {reason}")  
        except:   
            pass  
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка: Время должно быть числом."
        )
        return  
  
@bot.message_handler(commands=['unmute'])  
def unmute_command(message):  
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:   
        return  
          
    args = message.text.split()  
    if len(args) < 2:   
        return bot.send_message(message.chat.id, "❌ Формат: `/unmute @user`", parse_mode="Markdown")  
      
    target_id = get_user_id(args[1])  
    if target_id in mutes:  
        del mutes[target_id]  
        save_data()  
        bot.send_message(message.chat.id, f"✅ Мут с пользователя {args[1]} снят.")  
        try:   
            bot.send_message(int(target_id), "🔊 Ваш мут был снят.")  
        except:   
            pass  
    else:   
        bot.send_message(message.chat.id, "❌ У этого пользователя нет мута.")  
  
@bot.message_handler(commands=['ban'])  
def ban_command(message):  
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:   
        return  
          
    args = message.text.split()  
    if len(args) < 2:   
        return bot.send_message(message.chat.id, "❌ Формат: `/ban @user`", parse_mode="Markdown")  
      
    target_id = get_user_id(args[1])  
    if not target_id:   
        return bot.send_message(message.chat.id, "❌ Пользователь не найден.")  
      
    bans.add(target_id)  
    save_data()  
    bot.send_message(message.chat.id, f"✅ Пользователь {args[1]} забанен навсегда.")  
    try:   
        bot.send_message(int(target_id), "🚫 Вы были заблокированы в боте.")  
    except:   
        pass  
  
@bot.message_handler(commands=['unban'])  
def unban_command(message):  
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:   
        return  
          
    args = message.text.split()  
    if len(args) < 2:   
        return bot.send_message(message.chat.id, "❌ Формат: `/unban @user`")  
      
    target_id = get_user_id(args[1])  
    if target_id in bans:  
        bans.remove(target_id)  
        save_data()  
        bot.send_message(message.chat.id, f"✅ Пользователь {args[1]} разбанен.")  
    else:   
        bot.send_message(message.chat.id, "❌ Пользователь не в бане.")  
  
# 🔥 1. ИСПРАВЛЕННАЯ КОМАНДА /NLIST (ЮЗЕРНЕЙМЫ)  
@bot.message_handler(commands=['nlist'])  
def nlist_command(message):  
    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:   
        return  
          
    text = "👮‍♂️ **Список модераторов рынка:**\n\n"  
    id_to_name_map = {str(val): key for key, val in usernames.items()}  
    current_moderators = sorted(list(MODS))  
      
    for i, mod_id in enumerate(current_moderators, 1):  
        m_id_str = str(mod_id)  
        uname = id_to_name_map.get(m_id_str)  
          
        if uname:  
            text += f"{i}. @{uname}\n"  
        else:  
            text += f"{i}. ID: `{mod_id}` (не найден в базе имен)\n"  
              
    bot.send_message(message.chat.id, text, parse_mode="Markdown")  
  
# 🔥 КОМАНДЫ ДЛЯ SUPERADMIN  
@bot.message_handler(commands=['setadmin'])  
def setadmin_command(message):  
    if message.from_user.id != SUPERADMIN:  
        return  
  
    args = message.text.split()  
    if len(args) < 2:  
        return bot.send_message(message.chat.id, "❌ Формат: `/setadmin @user`", parse_mode="Markdown")  
  
    username = args[1].replace("@", "")  
    uid = get_user_id(username)  
  
    if not uid:  
        return bot.send_message(message.chat.id, "❌ Юзер не найден. Он должен запустить бота.")  
  
    uid = int(uid)  
  
    if uid in MODS:  
        return bot.send_message(message.chat.id, "❌ Пользователь уже модератор.")  
  
    MODS.add(uid)  
    save_data()  
    bot.send_message(message.chat.id, f"✅ @{username} теперь модератор.")  
  
    try:  
        bot.send_message(uid, "🎉 Поздравляем! Вы назначены модератором.\n\n📌 Ознакомьтесь с командами: /help")  
    except:  
        pass  
  
@bot.message_handler(commands=['deladmin'])  
def deladmin_command(message):  
    if message.from_user.id != SUPERADMIN:  
        return  
  
    args = message.text.split()  
    if len(args) < 2:  
        return bot.send_message(message.chat.id, "❌ Формат: `/deladmin @user`", parse_mode="Markdown")  
  
    username = args[1].replace("@", "")  
    uid = get_user_id(username)  
  
    if not uid:  
        return bot.send_message(message.chat.id, "❌ Юзер не найден.")  
  
    uid = int(uid)  
  
    if uid not in MODS:  
        return bot.send_message(message.chat.id, "❌ Не является модератором.")  
  
    MODS.discard(uid)  
    save_data()  
    bot.send_message(message.chat.id, f"✅ @{username} снят с должности.")  
  
    try:  
        bot.send_message(uid, "⚠️ К сожалению, вы сняты с должности модератора.")  
    except:  
        pass  
  
# 🔥 2. ИСПРАВЛЕННАЯ КОМАНДА /ALL (ФОТО/ВИДЕО/ТЕКСТ БЕЗ ПЕРЕСЫЛКИ)  
@bot.message_handler(commands=['all'])  
def broadcast_init(message):  
    if message.from_user.id != SUPERADMIN:   
        return  
      
    waiting_for_broadcast.add(message.from_user.id)  
    bot.send_message(message.chat.id, "📢 **Режим рассылки.**\nОтправьте сообщение (текст, фото или видео) и я разошлю его всем пользователям.", parse_mode="Markdown")  
  
@bot.message_handler(commands=['stats'])  
def stats_command(message):  
    if message.from_user.id != SUPERADMIN:   
        return  
          
    text = (  
        f"📊 **Статистика бота:**\n\n"  
        f"👥 Всего в базе: **{len(users)}**\n"  
        f"👮‍♂️ Модераторов: **{len(MODS)}**\n"  
        f"🚫 Забанено: **{len(bans)}**\n"  
        f"🔇 В муте: **{len([m for m in mutes if mutes[m] > time.time()])}**"  
    )  
    bot.send_message(message.chat.id, text, parse_mode="Markdown")  
  
# 🔥 ПЕРЕХВАТ НЕВЕРНЫХ КОМАНД  
@bot.message_handler(func=lambda message: message.text and message.text.startswith('/'))  
def unknown_cmd(message):  
    bot.send_message(message.chat.id, "❌ Команда не распознана.")  
  
# 🔥📩 ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ (ГЛАВНАЯ ЛОГИКА)  
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'voice', 'audio'])  
def handle_everything(message):  
    uid = message.from_user.id  
    uid_str = str(uid)  
    user_identity = message.from_user.username or message.from_user.first_name  
  
    # 1. Проверки на бан и мут, перенесенные внутрь функции  
    if uid_str in bans:   
        return  
          
    if uid_str in mutes:  
        if time.time() < mutes[uid_str]:  
            remaining = int((mutes[uid_str] - time.time()) / 60)  
            bot.send_message(uid, f"🔇 Вы в муте. Осталось: {remaining} мин.")  
            return  
        else:  
            del mutes[uid_str]  
            save_data()  
  
    # Обработка рассылки /all  
    if uid == SUPERADMIN and uid in waiting_for_broadcast:  
        waiting_for_broadcast.remove(uid)  
        bot.send_message(message.chat.id, "⏳ Рассылка запущена...")  
          
        success_count = 0  
        for target_id in users:  
            try:  
                bot.copy_message(int(target_id), message.chat.id, message.message_id)  
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
  
    # 🛡 3. ИСПРАВЛЕННЫЙ ЧАТ МОДЕРАТОРОВ (ВИДЯТ ВСЕ)  
    if uid in MODS or uid == SUPERADMIN:  
        all_mods_list = MODS.union({SUPERADMIN})  
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
  
    # Генерация ID поста  
    p_id = str(int(time.time() * 1000))  
  
    # Работа с альбомами
if message.media_group_id:
    group_id = message.media_group_id

    if group_id not in media_groups:
        media_groups[group_id] = []

    media_groups[group_id].append(message)

    # ждём пока Telegram докинет остальные фото
    time.sleep(2)

    # если альбом уже обработан
    if group_id not in media_groups:

    messages_in_group = media_groups.pop(group_id)

    if not messages_in_group:
        return

    main_caption = messages_in_group[0].caption or ""

    # проверка username
    if "@" not in main_caption:
        bot.send_message(
            uid,
            "❌ Ошибка: В описании альбома должен быть ваш @username!"
        )
        return

   # Логика АЛЬБОМОВ (Media Group)  
    if message.media_group_id:  
        mg_id = message.media_group_id  
        if mg_id not in media_groups:  
            media_groups[mg_id] = [message]  
            bot.send_message(uid, "⏳ Сбор файлов альбома... Ожидайте.")  
            
            # Ждем 2 секунды, пока Telegram дошлет все части альбома  
            time.sleep(2)  
              
            msgs = media_groups.pop(mg_id, [])  
            if not msgs: return  
  
            caption = ""  
            album_items = []  
            for m in msgs:  
                if m.caption: caption = m.caption  
                if m.photo:  
                    album_items.append(types.InputMediaPhoto(m.photo[-1].file_id))  
                elif m.video:  
                    album_items.append(types.InputMediaVideo(m.video.file_id))  
  
            if "@" not in caption:  
                bot.send_message(uid, "❌ Ошибка: Укажите ваш @username в описании!")  
                return  
  
            p_id = str(int(time.time() * 1000))  
            pending_posts[p_id] = {  
                "type": "album", "chat_id": message.chat.id, "user_id": uid,   
                "media": album_items, "caption": caption  
            }  
  
            notify_mods_media(album_items, caption, p_id, user_tag, "Альбом")  
            bot.send_message(uid, "✅ Альбом отправлен на модерацию!")  
        else:  
            media_groups[mg_id].append(message)  
        return  
  
    # Логика ОДИНОЧНЫХ сообщений  
    else:  
        caption = message.caption or message.text or ""  
        if "@" not in caption:  
            bot.send_message(uid, "❌ Ошибка: В тексте должен быть ваш @username!")  
            return  
  
        p_id = str(int(time.time() * 1000))  
        content_type = message.content_type  
          
        file_id = None  
        if message.photo: file_id = message.photo[-1].file_id  
        elif message.video: file_id = message.video.file_id  
  
        pending_posts[p_id] = {  
            "type": content_type, "chat_id": message.chat.id, "user_id": uid,  
            "message_id": message.message_id, "caption": caption, "file_id": file_id  
        }  
  
        # Отправляем модераторам  
        notify_mods_media(file_id if file_id else None, caption, p_id, user_tag, content_type)  
        bot.send_message(uid, "✅ Сообщение отправлено на модерацию!")  
  
if __name__ == '__main__':  
    print("Бот запущен...")  
    bot.infinity_polling()
