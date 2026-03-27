# bot.py
import telebot
import os
from flask import Flask, request

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")  # Set this in Railway secrets
if not TOKEN:
    raise ValueError("Bot token is missing! Set BOT_TOKEN in Railway secrets.")

# ================= DEVICE VERIFICATION =================
# Telegram user_id -> device/session ID mapping
VERIFIED_USERS = {
    123456789: "DEVICE_ABC123",  # Replace with real user IDs
    987654321: "DEVICE_XYZ987"
}

# ================= TELEGRAM BOT =================
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ================= FLASK APP =================
app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Bot is running", 200

# ================= BOT COMMANDS =================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    device_id = str(message.from_user.id)  # simple device simulation
    allowed_device = VERIFIED_USERS.get(user_id)
    
    if not allowed_device or allowed_device != device_id:
        bot.send_message(message.chat.id, "❌ You are not verified or using an unauthorized device.")
        return
    
    bot.send_message(message.chat.id, f"✅ Welcome! Your device is verified, {message.from_user.first_name}.")

@bot.message_handler(commands=['verify'])
def verify(message):
    secret_code = "1234"  # your secret verification code
    args = message.text.split()
    
    if len(args) != 2:
        bot.send_message(message.chat.id, "Usage: /verify <code>")
        return
    
    if args[1] == secret_code:
        device_id = str(message.from_user.id)
        VERIFIED_USERS[message.from_user.id] = device_id
        bot.send_message(message.chat.id, "✅ Your device is now verified!")
    else:
        bot.send_message(message.chat.id, "❌ Invalid verification code.")

# ================= WEBHOOK SETUP =================
def set_webhook():
    url = os.getenv("RAILWAY_STATIC_URL")  # Railway public URL
    if not url:
        raise ValueError("RAILWAY_STATIC_URL is missing! Set it in Railway environment variables.")
    webhook_url = f"{url}/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print("Webhook set:", webhook_url)

# ================= RUN =================
if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
