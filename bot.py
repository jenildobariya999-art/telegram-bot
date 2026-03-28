# bot.py
from flask import Flask, request
import telebot
import os

# -------------------------
# CONFIG
# -------------------------
TOKEN = "8274297339:AAHfc0y2cXcaOxSFzYNYmY5-oOf2ESIuemg"
WEBHOOK_URL = f"https://verification-beta-five.vercel.app/{TOKEN}"  # Replace with your actual URL
ADMIN_IDS = [6925391837, 7528813331]  # Add admin IDs here

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# -------------------------
# BOT COMMANDS
# -------------------------

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, f"Hello {message.from_user.first_name}! Bot is now active ✅")

@bot.message_handler(commands=["adminpanel"])
def admin_panel(message):
    if message.from_user.id in ADMIN_IDS:
        bot.reply_to(message, "Welcome to the Admin Panel!\nOptions:\n1. Broadcast\n2. Add/Remove Admin\n3. Check Fund")
    else:
        bot.reply_to(message, "You are not authorized to access this panel ❌")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, f"You said: {message.text}")

# -------------------------
# WEBHOOK HANDLER
# -------------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# -------------------------
# REMOVE OLD WEBHOOK & SET NEW
# -------------------------
@app.route("/setwebhook", methods=["GET", "POST"])
def set_webhook():
    bot.remove_webhook()
    success = bot.set_webhook(url=WEBHOOK_URL)
    if success:
        return "Webhook setup successful ✅"
    else:
        return "Webhook setup failed ❌"

# -------------------------
# RUN FLASK
# -------------------------
if __name__ == "__main__":
    # For production use, don't use debug=True
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
