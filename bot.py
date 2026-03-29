from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import threading

TOKEN = "8274297339:AAEch3qco73oPdck8vMIROqJxfAj0SARyU8"
WEB_URL = "https://verification-beta-five.vercel.app"  # Vercel link

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

verified_devices = {}

# ✅ VERIFY API
@app.route("/verify", methods=["POST"])
def verify():
    try:
        data = request.json
        user_id = str(data.get("user_id"))
        fingerprint = data.get("fingerprint")

        # 🟢 FIRST TIME ALWAYS SUCCESS
        if user_id not in verified_devices:
            verified_devices[user_id] = fingerprint

            try:
                bot.send_message(user_id, "✅ Verification Successful!")
            except:
                pass

            return jsonify({"status": "success"})

        # 🔴 SAME USER AGAIN
        if verified_devices[user_id] == fingerprint:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "failed"})

    except:
        return jsonify({"status": "failed"})


@app.route("/")
def home():
    return "Running ✅"


# 🤖 START COMMAND (🔥 WEB APP BUTTON)
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "🔐 Verify Device",
            web_app=WebAppInfo(f"{WEB_URL}?id={user_id}")
        )
    )

    bot.send_message(
        msg.chat.id,
        "🔐 Click below to verify",
        reply_markup=markup
    )


def run_bot():
    bot.infinity_polling(skip_pending=True)


threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
