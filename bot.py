from flask import Flask, request, jsonify
import telebot
import threading
import time

app = Flask(__name__)

TOKEN = "8274297339:AAEch3qco73oPdck8vMIROqJxfAj0SARyU8"
bot = telebot.TeleBot(TOKEN)

WEB_URL = "https://verification-beta-five.vercel.app"

# storage (no DB)
users = {}
used_tokens = {}

def generate_token(user_id):
    return f"{user_id}_{int(time.time())}"

@app.route("/")
def home():
    return "OK"

@app.route("/verify", methods=["POST"])
def verify():
    try:
        data = request.json

        user_id = str(data.get("user_id"))
        token = data.get("token")
        fingerprint = data.get("fingerprint")

        ip = request.remote_addr

        # ❌ Token reuse
        if token in used_tokens:
            return jsonify({"status": "failed", "reason": "Link used"})

        # ❌ Already verified check
        if user_id in users:
            saved = users[user_id]

            if saved["ip"] != ip:
                return jsonify({"status": "failed", "reason": "IP changed"})

            if saved["fingerprint"] != fingerprint:
                return jsonify({"status": "failed", "reason": "Device changed"})

            return jsonify({"status": "failed", "reason": "Already verified"})

        # ✅ Save first time
        users[user_id] = {
            "ip": ip,
            "fingerprint": fingerprint
        }

        used_tokens[token] = True

        bot.send_message(int(user_id), "✅ Verification Successful!")

        return jsonify({"status": "success"})

    except:
        return jsonify({"status": "failed", "reason": "Verification failed"})

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.chat.id
    token = generate_token(user_id)

    url = f"{WEB_URL}?id={user_id}&token={token}"

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Verify Device", url=url)
    )

    bot.send_message(user_id, "Click to verify:", reply_markup=markup)

def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
