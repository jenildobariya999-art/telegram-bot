import os
from flask import Flask, request
from telebot import TeleBot
import json

# ===== CONFIG =====
TOKEN = "8274297339:AAHfc0y2cXcaOxSFzYNYmY5-oOf2ESIuemg"  # Replace with your bot token
bot = TeleBot(TOKEN)

ADMINS = [6925391837, 7528813331]
VERCEL_WEBAPP_URL = "https://verification-beta-five.vercel.app"
RAILWAY_BACKEND_URL = "https://web-production-0df8e.up.railway.app"

# In-memory storage for devices (use DB for production)
used_devices = {}  # device_hash: user_id

# ===== FLASK APP =====
app = Flask(__name__)

# ===== TELEGRAM COMMANDS =====
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    bot.send_message(
        user_id,
        f"Hello {first_name}! Please verify yourself.\n\nClick below to verify:",
        reply_markup={
            "inline_keyboard": [
                [
                    {
                        "text": "Verify Now",
                        "web_app": {"url": VERCEL_WEBAPP_URL}
                    }
                ]
            ]
        }
    )

# ===== WEBAPP VERIFICATION =====
@app.route("/verify", methods=["POST"])
def verify_device():
    data = request.json
    user_id = data.get("user_id")
    device = data.get("device")

    # Use device JSON string as unique device key
    device_key = json.dumps(device, sort_keys=True)

    # Check if device already used by another user
    if device_key in used_devices and used_devices[device_key] != user_id:
        return {"status": "failed"}

    # Mark device as used by this user
    used_devices[device_key] = user_id

    return {"status": "success"}

# ===== WEBHOOK TO RECEIVE RESULT =====
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    chat_id = data.get("chat_id")
    result = data.get("result")
    device_info = data.get("device_info")

    if result == "success":
        bot.send_message(chat_id, "✅ Verification Successful! Device approved.")
    else:
        bot.send_message(chat_id, "❌ Verification Failed! Device already used.")

    # Notify admins
    for admin in ADMINS:
        bot.send_message(
            admin,
            f"User: {chat_id}\nResult: {result}\nDevice: {device_info}"
        )

    return {"status": "ok"}

# ===== RUN TELEBOT POLLING =====
if __name__ == "__main__":
    import threading

    # Start TeleBot polling in separate thread
    threading.Thread(target=lambda: bot.infinity_polling()).start()

    # Run Flask server for webhooks
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
