import telebot
import time
import re
import os

TOKEN = os.getenv("TOKEN", "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30)

bot = telebot.TeleBot(TOKEN)

MODS = [7905149857]

users = {}
bans = {}
mutes = {}


def is_mod(user_id):
    return user_id in MODS


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if user_id not in users:
        users[user_id] = {"firstSeen": time.time(), "count": 0}

    bot.send_message(
        user_id,
        "Привет!\nДобро пожаловать в БУ рынок.\n\nОтправь объявление.\nПроверка модераторами."
    )


@bot.message_handler(commands=['help'])
def help_cmd(message):
    if not is_mod(message.from_user.id):
        bot.send_message(message.chat.id, "Нет доступа")
        return

    bot.send_message(
        message.chat.id,
        "/stats\n/ban (reply)\n/mute 10 (reply)"
    )


@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if not is_mod(message.from_user.id):
        return

    bot.send_message(message.chat.id, f"Пользователей: {len(users)}")


@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if not is_mod(message.from_user.id):
        return

    if not message.reply_to_message:
        return

    match = re.search(r"ID:\s*(\d+)", message.reply_to_message.text or "")
    if not match:
        return

    uid = int(match.group(1))
    bans[uid] = True
    bot.send_message(uid, "Вас забанили")


@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if not is_mod(message.from_user.id):
        return

    if not message.reply_to_message:
        return

    parts = message.text.split()
    if len(parts) < 2:
        return

    match = re.search(r"ID:\s*(\d+)", message.reply_to_message.text or "")
    if not match:
        return

    uid = int(match.group(1))
    mins = int(parts[1])

    mutes[uid] = time.time() + mins * 60
    bot.send_message(uid, f"Мут на {mins} минут")


@bot.message_handler(func=lambda m: True)
def all_messages(message):
    user_id = message.from_user.id
    text = message.text

    if not text:
        return

    if text.startswith("/"):
        return

    if user_id in bans:
        return

    if user_id in mutes and time.time() < mutes[user_id]:
        bot.send_message(user_id, "У вас мут")
        return

    if user_id not in users:
        users[user_id] = {"firstSeen": time.time(), "count": 0}

    users[user_id]["count"] += 1

    username = message.from_user.username or "no_username"

    bot.send_message(user_id, "Ожидайте проверку")

    info = f"Новое объявление\n@{username}\nID: {user_id}\n#{users[user_id]['count']}"

    for mod in MODS:
        bot.send_message(mod, info)
        bot.forward_message(mod, message.chat.id, message.message_id)


if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)
