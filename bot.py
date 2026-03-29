from flask import Flask, request, jsonify
import telebot
import threading

app = Flask(__name__)

TOKEN = "8274297339:AAEch3qco73oPdck8vMIROqJxfAj0SARyU8"
bot = telebot.TeleBot(TOKEN)

WEB_URL = "https://verification-beta-five.vercel.app"

@app.route("/")
def home():
    return "Backend Working ✅"

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"status": "error"})

    bot.send_message(user_id, "✅ Verification Successful!")
    return jsonify({"status": "success"})

@bot.message_handler(commands=['start'])
def start(msg):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            "✅ Verify Device", 
            url=WEB_URL + f"?id={msg.chat.id}"
        )
    )
    bot.send_message(msg.chat.id, "Click below to verify:", reply_markup=markup)

def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
