import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8274297339:AAEch3qco73oPdck8vMIROqJxfAj0SARyU8"
bot = telebot.TeleBot(TOKEN)

WEB_URL = "https://verification-beta-five.vercel.app"  # IMPORTANT HTTPS

@bot.message_handler(commands=['start'])
def start(msg):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Verify Device", url=WEB_URL))
    bot.send_message(msg.chat.id, "Click below to verify:", reply_markup=markup)

print("Bot running...")
bot.infinity_polling(skip_pending=True)
