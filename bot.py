import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8274297339:AAEch3qco73oPdck8vMIROqJxfAj0SARyU8"
WEB_URL = "https://verification-beta-five.vercel.app"  # apna Vercel link

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "🔐 Verify Device",
            url=f"{WEB_URL}?id={user_id}"
        )
    )

    bot.send_message(
        msg.chat.id,
        "🔐 Please verify your device to continue",
        reply_markup=markup
    )

print("Bot Running...")
bot.infinity_polling(skip_pending=True)
