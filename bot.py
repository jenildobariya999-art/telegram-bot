import os
import telebot
from flask import Flask, request, redirect, render_template_string

# ===== CONFIG =====
TOKEN = os.getenv("BOT_TOKEN")  # Add your bot token in Railway env
RAILWAY_URL = os.getenv("RAILWAY_STATIC_URL")  # Your Railway app URL

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ===== In-memory store for verification status =====
pending_verification = {}

# ===== Web page template =====
VERIFY_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot Verification</title>
</head>
<body>
    <h2>Bot Verification</h2>
    <p>{{ message }}</p>
</body>
</html>
"""

# ===== Web route for verification =====
@app.route('/verify/<int:user_id>')
def verify_user(user_id):
    if user_id in pending_verification:
        # Mark verified
        pending_verification[user_id] = True
        # Notify bot
        bot.send_message(user_id, "✅ Verification Successful!")
        return render_template_string(VERIFY_PAGE, message="✅ Verification Successful! Return to Telegram.")
    else:
        return render_template_string(VERIFY_PAGE, message="❌ Verification Failed!")

# ===== Bot handlers =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Add user to pending verification
    pending_verification[user_id] = False
    # Send button with web link
    markup = telebot.types.InlineKeyboardMarkup()
    url_button = telebot.types.InlineKeyboardButton(
        text="Verify Now", 
        url=f"{RAILWAY_URL}/verify/{user_id}"
    )
    markup.add(url_button)
    bot.send_message(message.chat.id, "Please verify yourself to use this bot.", reply_markup=markup)

# ===== Webhook route =====
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

# ===== Set webhook =====
def set_webhook():
    webhook_url = f"{RAILWAY_URL}/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print("Webhook set:", webhook_url)

# ===== Run app =====
if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
