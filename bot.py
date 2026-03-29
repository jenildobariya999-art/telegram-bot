from flask import Flask, request, jsonify
import telebot
import threading
import requests
import time

app = Flask(__name__)

TOKEN = "8274297339:AAEch3qco73oPdck8vMIROqJxfAj0SARyU8"
bot = telebot.TeleBot(TOKEN)

WEB_URL = "https://verification-beta-five.vercel.app"

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

        user_id = int(data.get("user_id"))
        token = data.get("token")
        fingerprint = data.get("fingerprint")

        ip = request.remote_addr
        ua = request.headers.get("User-Agent", "")

        # ❌ Token reuse
        if token in used_tokens:
            return jsonify({"status": "failed", "reason": "Link already used"})

        # ❌ Bot detect
        if "bot" in ua.lower():
            return jsonify({"status": "failed", "reason": "Bot detected"})

        # ❌ VPN detect (REAL API)
        try:
            ip_data = requests.get(f"http://ip-api.com/json/{ip}").json()
            if ip_data.get("proxy") or ip_data.get("hosting"):
                return jsonify({"status": "failed", "reason": "VPN/Proxy detected"})
        except:
            pass  # agar API fail ho, ignore

        # Save token
        used_tokens[token] = True

        bot.send_message(user_id, "✅ Verification Successful!")

        return jsonify({"status": "success"})

    except Exception:
        # ❗ kabhi bhi crash nahi hone dena
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

    bot.send_message(user_id, "Click below to verify:", reply_markup=markup)

def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
