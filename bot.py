from flask import Flask, request, jsonify
from telebot import TeleBot, types
import hashlib, json, os, threading

API_TOKEN = os.environ.get("API_TOKEN")
DOMAIN = "https://verification-beta-five.vercel.app"

bot = TeleBot(API_TOKEN)
bot.remove_webhook()

app = Flask(__name__)

devices = {}
ips = {}
users = {}
failed = {}

# ===== HELPERS =====
def make_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

def get_ip(req):
    if req.headers.get("X-Forwarded-For"):
        return req.headers.get("X-Forwarded-For").split(",")[0]
    return req.remote_addr

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.chat.id)

    if uid in users:
        bot.send_message(uid, "✅ Already Verified")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🔐 Verify",
        web_app=types.WebAppInfo(DOMAIN)
    ))

    bot.send_message(uid, "🔐 Click below to verify", reply_markup=markup)

# ===== VERIFY API =====
@app.route("/verify", methods=["POST"])
def verify():
    try:
        data = request.json
        uid = str(data.get("user_id"))
        dev = make_hash(data.get("device"))
        ip = get_ip(request)

        if dev in devices or ip in ips:
            failed[uid] = True
            return jsonify({"status": "failed"})

        devices[dev] = uid
        ips[ip] = uid
        users[uid] = True

        bot.send_message(uid, "✅ Verification Successful")
        return jsonify({"status": "success"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error"})

# ===== RUN =====
def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot).start()

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
