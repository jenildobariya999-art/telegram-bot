from flask import Flask, request, jsonify
import telebot
import threading

TOKEN = "8274297339:AAEch3qco73oPdck8vMIROqJxfAj0SARyU8"
WEB_URL = "https://verification-beta-five.vercel.app"  # apna vercel link

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# simple memory database
verified_devices = {}

# 🔐 VERIFY API
@app.route("/verify", methods=["POST"])
def verify():
    try:
        data = request.json

        user_id = str(data.get("user_id"))
        fingerprint = data.get("fingerprint")

        # already used fingerprint
        if fingerprint in verified_devices.values():
            return jsonify({"status": "failed"})

        verified_devices[user_id] = fingerprint

        # send telegram success msg
        try:
            bot.send_message(user_id, "✅ Verification Successful!")
        except:
            pass

        return jsonify({"status": "success"})

    except:
        return jsonify({"status": "failed"})


@app.route("/")
def home():
    return "Bot Running ✅"


# 🤖 BOT START
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id

    link = f"{WEB_URL}?id={user_id}"

    bot.send_message(
        msg.chat.id,
        f"🔐 Click below to verify:\n{link}"
    )


def run_bot():
    bot.infinity_polling(skip_pending=True)


# run bot in thread
threading.Thread(target=run_bot).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
