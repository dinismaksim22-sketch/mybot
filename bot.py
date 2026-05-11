import telebot
import time
import json
import os
from telebot import types

# --- КОНФИГУРАЦИЯ ---

TOKEN = "8454142474:AAEK9wh21QXLE07pp33iwdtrFOJQ2zM23f4"
bot = telebot.TeleBot(TOKEN)

SUPERADMIN = 7905149857
DATA_FILE = "data.json"
CHANNEL_ID = "@br_bu_astana"

# 🔥 СТРУКТУРЫ ДАННЫХ И ЛОГИКА ФАЙЛОВ

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "mods": [SUPERADMIN],
            "users": {},
            "usernames": {},
            "bans": [],
            "mutes": {}
        }

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

        return {
            "mods": [SUPERADMIN],
            "users": {},
            "usernames": {},
            "bans": [],
            "mutes": {}
        }


def save_data():
    global data

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
waiting_for_broadcast = set()  # Для команды /all


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
        types.InlineKeyboardButton(
            "❌ Отказать",
            callback_data=f"reject_{post_id}"
        ),
        types.InlineKeyboardButton(
            "✅ Одобрить",
            callback_data=f"approve_{post_id}"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "💬 Написать участнику",
            callback_data=f"msg_{post_id}"
        )
    )

    return kb


# 🔥 CALLBACK ОБРАБОТЧИК

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):

    try:
        data_cb = call.data
        mod_name = call.from_user.username or call.from_user.first_name

        # =========================
        # ОДОБРЕНИЕ ПОСТА
        # =========================

        if data_cb.startswith("approve_"):

            post_id = data_cb.split("_")[1]
            post = pending_posts.get(post_id)

            if not post:
                bot.answer_callback_query(
                    call.id,
                    "❌ Ошибка: Пост не найден в очереди!",
                    show_alert=True
                )
                return

            bot.answer_callback_query(
                call.id,
                "✅ Публикация..."
            )

            try:

                # Публикация в канал
                if post["type"] in ["text", "photo", "video"]:

                    # Копируем сообщение пользователя
                    bot.copy_message(
                        chat_id=CHANNEL_ID,
                        from_chat_id=post["chat_id"],
                        message_id=post["message_id"]
                    )

                elif post["type"] == "album":

                    # Отправляем альбом
                    bot.send_media_group(
                        chat_id=CHANNEL_ID,
                        media=post["media"]
                    )

                # Сообщение пользователю
                try:
                    bot.send_message(
                        post["user_id"],
                        "✅ Ваше объявление успешно опубликовано!"
                    )

                except Exception:
                    pass

                # Уведомление модераторам
                try:
                    notify_mods(
                        f"✅ Модератор @{mod_name} одобрил объявление."
                    )

                except Exception:
                    pass

                # Убираем кнопки
                try:
                    bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=None
                    )

                except Exception:
                    pass

                # Удаляем из очереди
                pending_posts.pop(post_id, None)

            except Exception as e:

                bot.send_message(
                    call.message.chat.id,
                    f"❌ Ошибка отправки в канал:\n{e}"
                )

        # =========================
        # ОТКЛОНЕНИЕ ПОСТА
        # =========================

        elif data_cb.startswith("reject_"):

            post_id = data_cb.split("_")[1]

            if post_id not in pending_posts:

                bot.answer_callback_query(
                    call.id,
                    "❌ Пост уже обработан.",
                    show_alert=True
                )

                return

            waiting_for_reject[call.from_user.id] = post_id

            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                "✍️ Введите причину отказа (будет отправлено пользователю):"
            )

        # =========================
        # СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЮ
        # =========================

        elif data_cb.startswith("msg_"):

            post_id = data_cb.split("_")[1]

            if post_id not in pending_posts:

                bot.answer_callback_query(
                    call.id,
                    "❌ Пост уже обработан.",
                    show_alert=True
                )

                return

            waiting_for_msg[call.from_user.id] = post_id

            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                "✍️ Напишите текст сообщения для участника:"
            )

    # =========================
    # ОБЩАЯ ОШИБКА
    # =========================

    except Exception as e:

        try:
            bot.answer_callback_query(
                call.id,
                "⚠️ Системный сбой!",
                show_alert=True
            )

        except Exception:
            pass

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
        "Если у тебя не установлен @username в профиле Telegram — бот НЕ пропустит объявление.\n\n"
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

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown"
    )


# 🔥 УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ

@bot.message_handler(commands=['id'])
def get_user_id_cmd(message):

    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:
        return

    args = message.text.split()

    if len(args) < 2:
        return bot.send_message(
            message.chat.id,
            "❌ Формат: `/id @user`",
            parse_mode="Markdown"
        )

    target_id = get_user_id(args[1])

    if target_id:
        bot.send_message(
            message.chat.id,
            f"🔍 ID пользователя {args[1]}: `{target_id}`",
            parse_mode="Markdown"
        )

    else:
        bot.send_message(
            message.chat.id,
            "❌ Пользователь не найден в базе."
        )


# 🔥 MUTE

@bot.message_handler(commands=['mute'])
def mute_command(message):

    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:
        return

    args = message.text.split(maxsplit=3)

    if len(args) < 3:
        return bot.send_message(
            message.chat.id,
            "❌ Формат: `/mute @user время_в_минутах причина`",
            parse_mode="Markdown"
        )

    target_id = get_user_id(args[1])

    if not target_id:
        return bot.send_message(
            message.chat.id,
            "❌ Пользователь не найден."
        )

    try:
        minutes = int(args[2])
        reason = args[3] if len(args) > 3 else "Не указана"

        mutes[target_id] = time.time() + (minutes * 60)

        save_data()

        bot.send_message(
            message.chat.id,
            f"✅ Пользователь {args[1]} замучен на {minutes} мин.\n📋 Причина: {reason}"
        )

        try:
            bot.send_message(
                int(target_id),
                f"🔇 Вы получили мут на {minutes} минут.\n📋 Причина: {reason}"
            )

        except:
            pass

    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка: Время должно быть числом."
        )

        return


# 🔥 UNMUTE

@bot.message_handler(commands=['unmute'])
def unmute_command(message):

    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:
        return

    args = message.text.split()

    if len(args) < 2:
        return bot.send_message(
            message.chat.id,
            "❌ Формат: `/unmute @user`",
            parse_mode="Markdown"
        )

    target_id = get_user_id(args[1])

    if target_id in mutes:

        del mutes[target_id]

        save_data()

        bot.send_message(
            message.chat.id,
            f"✅ Мут с пользователя {args[1]} снят."
        )

        try:
            bot.send_message(
                int(target_id),
                "🔊 Ваш мут был снят."
            )

        except:
            pass

    else:
        bot.send_message(
            message.chat.id,
            "❌ У этого пользователя нет мута."
        )


# 🔥 BAN

@bot.message_handler(commands=['ban'])
def ban_command(message):

    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:
        return

    args = message.text.split()

    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ Формат: /ban @user")
        return

    target_id = get_user_id(args[1])

    if not target_id:
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")
        return

    bans.add(target_id)

    save_data()

    bot.send_message(
        message.chat.id,
        "✅ Пользователь забанен."
    )


# 🔥 UNBAN

@bot.message_handler(commands=['unban'])
def unban_command(message):

    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:
        return

    args = message.text.split()

    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ Формат: /unban @user")
        return

    target_id = get_user_id(args[1])

    if target_id in bans:

        bans.remove(target_id)

        save_data()

        bot.send_message(
            message.chat.id,
            "✅ Пользователь разбанен."
        )

    else:
        bot.send_message(
            message.chat.id,
            "❌ Пользователь не в бане."
        )


# 🔥 СПИСОК МОДЕРАТОРОВ

@bot.message_handler(commands=['nlist'])
def nlist_command(message):

    if message.from_user.id not in MODS and message.from_user.id != SUPERADMIN:
        return

    text = "👮‍♂️ *Модераторы:*\n\n"

    id_to_name_map = {
        str(v): k for k, v in usernames.items()
    }

    for i, mod_id in enumerate(sorted(MODS), 1):

        uname = id_to_name_map.get(str(mod_id))

        if uname:
            text += f"{i}. @{uname}\n"
        else:
            text += f"{i}. ID `{mod_id}`\n"

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown"
    )


# 🔥 SUPERADMIN

@bot.message_handler(commands=['setadmin'])
def setadmin_command(message):

    if message.from_user.id != SUPERADMIN:
        return

    args = message.text.split()

    if len(args) < 2:
        bot.send_message(
            message.chat.id,
            "❌ Формат: /setadmin @user"
        )
        return

    username = args[1]
    uid = get_user_id(username)

    if not uid:
        bot.send_message(
            message.chat.id,
            "❌ Пользователь не найден."
        )
        return

    uid = int(uid)

    MODS.add(uid)

    save_data()

    bot.send_message(
        message.chat.id,
        f"✅ @{username.replace('@', '')} теперь модератор."
    )


@bot.message_handler(commands=['deladmin'])
def deladmin_command(message):

    if message.from_user.id != SUPERADMIN:
        return

    args = message.text.split()

    if len(args) < 2:
        bot.send_message(
            message.chat.id,
            "❌ Формат: /deladmin @user"
        )
        return

    username = args[1]
    uid = get_user_id(username)

    if not uid:
        bot.send_message(
            message.chat.id,
            "❌ Пользователь не найден."
        )
        return

    uid = int(uid)

    MODS.discard(uid)

    save_data()

    bot.send_message(
        message.chat.id,
        f"✅ @{username.replace('@', '')} удален из модеров."
    )


# 🔥 РАССЫЛКА

@bot.message_handler(commands=['all'])
def broadcast_init(message):

    if message.from_user.id != SUPERADMIN:
        return

    waiting_for_broadcast.add(message.from_user.id)

    bot.send_message(
        message.chat.id,
        "📢 Отправьте сообщение для рассылки."
    )


# 🔥 СТАТИСТИКА

@bot.message_handler(commands=['stats'])
def stats_command(message):

    if message.from_user.id != SUPERADMIN:
        return

    text = (
        f"📊 Статистика:\n\n"
        f"👥 Пользователей: {len(users)}\n"
        f"👮 Модераторов: {len(MODS)}\n"
        f"🚫 Бан: {len(bans)}\n"
        f"🔇 Мут: {len(mutes)}"
    )

    bot.send_message(message.chat.id, text)


# 🔥 НЕИЗВЕСТНЫЕ КОМАНДЫ

@bot.message_handler(func=lambda message: message.text and message.text.startswith('/'))
def unknown_cmd(message):

    bot.send_message(
        message.chat.id,
        "❌ Команда не найдена."
    )


# 🔥 ГЛАВНЫЙ ОБРАБОТЧИК

@bot.message_handler(
    content_types=[
        'text',
        'photo',
        'video',
        'document',
        'voice',
        'audio'
    ]
)
def handle_everything(message):

    uid = message.from_user.id
    uid_str = str(uid)

    # БАН

    if uid_str in bans:
        return

    # МУТ

    if uid_str in mutes:

        if time.time() < mutes[uid_str]:

            remaining = int(
                (mutes[uid_str] - time.time()) / 60
            )

            bot.send_message(
                uid,
                f"🔇 Вы в муте. Осталось {remaining} мин."
            )

            return

        else:
            del mutes[uid_str]
            save_data()

    # РАССЫЛКА

    if uid == SUPERADMIN and uid in waiting_for_broadcast:

        waiting_for_broadcast.remove(uid)

        sent = 0

        bot.send_message(
            message.chat.id,
            "⏳ Рассылка началась..."
        )

        for target_id in users:

            try:
                bot.copy_message(
                    int(target_id),
                    message.chat.id,
                    message.message_id
                )

                sent += 1

            except Exception:
                pass

        bot.send_message(
            message.chat.id,
            f"✅ Отправлено: {sent}"
        )

        return

    # РЕГИСТРАЦИЯ

    register_user(message)

    # ПРОВЕРКА USERNAME

    if not message.from_user.username:

        bot.send_message(
            uid,
            "❌ Установите username в Telegram."
        )

        return

    # ПРОВЕРКА ТЕКСТА

    caption = message.caption or message.text or ""

    if "@" not in caption:

        bot.send_message(
            uid,
            "❌ Укажите @username в объявлении."
        )

        return

    # СОЗДАНИЕ ПОСТА

    p_id = str(int(time.time() * 1000))

    pending_posts[p_id] = {
        "type": message.content_type,
        "chat_id": message.chat.id,
        "user_id": uid,
        "message_id": message.message_id
    }

    # ОТПРАВКА МОДЕРАМ

    for mod_id in MODS.union({SUPERADMIN}):

        try:

            bot.copy_message(
                mod_id,
                message.chat.id,
                message.message_id
            )

            bot.send_message(
                mod_id,
                f"📢 Новое объявление\n👤 @{message.from_user.username}\n🆔 {uid}",
                reply_markup=mod_kb(p_id)
            )

        except Exception as e:
            print(e)

    bot.send_message(
        uid,
        "⏳ Объявление отправлено модераторам."
    )


# 🔥 ЗАПУСК

if __name__ == '__main__':

    print("Бот запущен...")

    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60
        )
