from flask import Flask, request
import telebot

TOKEN = "8274297339:AAHfc0y2cXcaOxSFzYNYmY5-oOf2ESIuemg"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

ADMINS = [6925391837, 7528813331]

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def index():
    return "Bot is running!", 200

# Optional: delete previous webhook if needed
bot.remove_webhook()
bot.set_webhook(url="https://verification-beta-five.vercel.app/" + TOKEN)

# DO NOT CALL bot.polling()
