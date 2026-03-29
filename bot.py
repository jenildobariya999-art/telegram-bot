from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import threading

TOKEN = "8274297339:AAEch3qco73oPdck8vMIROqJxfAj0SARyU8"
WEB_URL = "https://verification-beta-five.vercel.app"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 🔥 DEVICE BASED STORAGE
device_data = {}   # fingerprint → user_id

# ✅ VERIFY API
@app.route("/verify", methods=["POST"])
def verify():
    try:
        data = request.json
        user_id = str(data.get("user_id"))
        fingerprint = data.get("fingerprint")

        if not user_id or not fingerprint:
            return jsonify({"status": "failed"})

        # 🟢 NEW DEVICE
        if fingerprint not in device_data:
            device_data[fingerprint] = user_id

            try:
                bot.send_message(user_id, "✅ Verification Successful")
            except:
                pass

            return jsonify({"status": "success"})

        # 🟢 SAME DEVICE SAME USER
        if device_data[fingerprint] == user_id:
            return jsonify({"status": "success"})

        # 🔴 SAME DEVICE DIFFERENT USER
        return jsonify({"status": "failed"})

    except:
        return jsonify({"status": "failed"})


@app.route("/")
def home():
    return "Running ✅"


# 🤖 TELEGRAM START
@bot.message_handler(commands=['start'])
def start(msg):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "🔐 Verify Device",
            web_app=WebAppInfo(WEB_URL)
        )
    )

    bot.send_message(
        msg.chat.id,
        "🔐 Click below to verify your device",
        reply_markup=markup
    )


def run_bot():
    bot.infinity_polling(skip_pending=True)


threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
