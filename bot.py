const TelegramBot = require('node-telegram-bot-api');

const TOKEN = process.env.TOKEN;
const bot = new TelegramBot(TOKEN, { 8454142474:AAHpLFHANoCmQQpDTO7iZpDVXvbaPUqNr30});

// 👮 модеры
const MODS = [7905149857];

// базы
const users = {};
const bans = {};
const mutes = {};

// =====================
// /start
// =====================
bot.onText(/\/start/, (msg) => {
    const id = msg.from.id;

    if (!users[id]) {
        users[id] = {
            firstSeen: new Date(),
            count: 0
        };
    }

    bot.sendMessage(id,
`Привет! 👋
Добро пожаловать в БУ рынок.

Отправь объявление по форме.

❗Сообщения проверяются модераторами`
    );
});


// =====================
// 📩 ВСЕ СООБЩЕНИЯ
// =====================
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

const id = msg.from.id;
    if (!MODS.includes(id)) return;

    bot.sendMessage(id,
📊 Пользователей: ${Object.keys(users).length}
    );
});
