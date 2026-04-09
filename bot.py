Привет telebot

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "⏳ Ожидайте, все объявления проверяются модераторами, не нужно дублировать сообщение.")

bot.infinity_polling()
