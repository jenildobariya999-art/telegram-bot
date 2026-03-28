from flask import Flask, request
import telebot

TOKEN = "8274297339:AAHfc0y2cXcaOxSFzYNYmY5-oOf2ESIuemg"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

ADMINS = [6925391837, 7528813331]

# Webhook route
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# Test route
@app.route("/")
def index():
    return "Bot is running!", 200

# Example handler
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, f"Hello! Your ID: {message.from_user.id}")

# Remove previous webhook and set new one
bot.remove_webhook()
bot.set_webhook(url="https://verification-beta-five.vercel.app/" + TOKEN)
