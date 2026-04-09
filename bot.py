всеlebot
import time

TOKEN = "8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30"

bot = telebot.TeleBot(TOKEN)

MODS = [7905149857]  # сюда свой ID

users = {}
bans = {}
mutes = {}

# /start
@bot.message_handler(commands=['start'])
def start(message):
    id = message.from_user.id

    if id not in users:
        users[id] = {
            "firstSeen": time.time(),
            "count": 0
        }

    bot.send_message(
    id,
    "Привет! 👋\n"
    "Ты попал в Б/У рынок ASTANA.\n\n"
    
    "📌 Для подачи объявления обязательно укажи:\n"
    "1. Куплю / Продам / Набор в ТК или в семью\n"
    "2. Цена / Бюджет\n"
    "3. Контакт (username, пример: @cripta527)\n\n"
    
    "❗ Важно:\n"
    "Без username заявка будет отклонена.\n"
    "Все пункты должны быть заполнены по форме, иначе будет отказ.\n\n"
    
    "🚫 Не спамить\n"
    "Разрешена реклама семьи / СК / ТК и т.д.\n\n"
    
    "📩 Связь: @cripta527"
    )

# все сообщения
bot.on('message', (msg) => {
    const id = msg.from.id;
    const text = msg.text;

    if (!text) return;
    if (text.startsWith('/start')) return;

    // =====================
    // 👮 МОДЕРАТОРЫ
    // =====================
    if (MODS.includes(id)) {

        // =====================
        // 💬 ОТВЕТ ПОЛЬЗОВАТЕЛЮ
        // =====================
        if (msg.reply_to_message) {
            const match = msg.reply_to_message.text?.match(/ID:\s*(\d+)/);

            if (match) {
                const userId = match[1];
                bot.sendMessage(userId, text); // чистый ответ
                return;
            }
        }

        // =====================
        // 🛡 ЧАТ МОДЕРАТОРОВ
        // =====================
        MODS.forEach(mod => {
            if (mod !== id) {
                bot.sendMessage(
                    mod,
                    🛡 Модератор @${msg.from.username || "no_username"}:\n${text}
                );
            }
        });

        return;
    }

    // =====================
    // 🚫 БАН / МУТ
    // =====================
    if (bans[id]) return;

    if (mutes[id] && Date.now() < mutes[id]) {
        bot.sendMessage(id, "⛔ У вас мут.");
        return;
    }

    // =====================
    // 👤 РЕГИСТРАЦИЯ
    // =====================
    if (!users[id]) {
        users[id] = {
            firstSeen: new Date(),
            count: 0
        };
    }

    users[id].count++;

    const username = msg.from.username || "no_username";

    // =====================
    // ⏳ АВТООТВЕТ
    // =====================
    bot.sendMessage(id,
"⏳ Ожидайте, ваше объявление отправлено на проверку."
    );

    // =====================
    // 📢 МОДЕРАЦИЯ (ПЕРЕСЫЛКА КАК В TG)
    // =====================
    const info =
`📢 Новое объявление

👤 @${username}
🆔 ID: ${id}
📨 ${users[id].count}
📅 ${users[id].firstSeen.toLocaleString()}`;

    MODS.forEach(mod => {
        bot.sendMessage(mod, info);

        // 👇 ПРЯМАЯ ПЕРЕСЫЛКА (как в Telegram)
        bot.forwardMessage(mod, msg.chat.id, msg.message_id);
    });
});


// =====================
// 🛠 /help (ТОЛЬКО ДЛЯ МОДОВ)
// =====================
bot.onText(/\/help/, (msg) => {
    const id = msg.from.id;

    if (!MODS.includes(id)) {
        bot.sendMessage(id, "❌ Нет доступа.");
        return;
    }

    bot.sendMessage(id,
`🛠 МОДЕРАТОРЫ

/stats — статистика
/ban (reply)
/mute (reply)
/help`
    );
});


// =====================
// ⛔ BAN
// =====================
bot.onText(/\/ban/, (msg) => {
    const id = msg.from.id;
    if (!MODS.includes(id)) return;

    if (!msg.reply_to_message) return;

    const match = msg.reply_to_message.text?.match(/ID:\s*(\d+)/);
    if (!match) return;

    bans[match[1]] = true;
    bot.sendMessage(match[1], "⛔ Вас забанили.");
});


// =====================
// ⏳ MUTE
// =====================
bot.onText(/\/mute (\d+)/, (msg, match) => {
    const id = msg.from.id;
    if (!MODS.includes(id)) return;

    if (!msg.reply_to_message) return;

    const userMatch = msg.reply_to_message.text?.match(/ID:\s*(\d+)/);
    if (!userMatch) return;

    const mins = parseInt(match[1]);
    mutes[userMatch[1]] = Date.now() + mins * 60000;

    bot.sendMessage(userMatch[1], `⛔ Мут на ${mins} минут`);
});


// =====================
// 📊 STATS
// =====================
bot.onText(/\/stats/, (msg) => {
