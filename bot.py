from flask import Flask, request, jsonify
from flask_cors import CORS
from telebot import TeleBot, types
import hashlib, json, os, threading

API_TOKEN = os.environ.get("API_TOKEN")

# ✅ YOUR VERCEL LINK
DOMAIN = "https://verification-beta-five.vercel.app/"

ADMIN_IDS = ["6925391837", "7528813331"]

bot = TeleBot(API_TOKEN, parse_mode="HTML")
bot.remove_webhook()

app = Flask(__name__)
CORS(app)

devices = {}
users = {}
ips = {}

def make_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

def get_ip(req):
    if req.headers.get("X-Forwarded-For"):
        return req.headers.get("X-Forwarded-For").split(",")[0]
    return req.remote_addr

@app.route("/")
def home():
    return "Bot Running ✅"

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.chat.id

    if str(uid) in users:
        return bot.send_message(uid, "✅ Already Verified")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🔐 Verify",
        web_app=types.WebAppInfo(DOMAIN)
    ))

    bot.send_message(uid, "🛡 Please verify first", reply_markup=markup)

# ===== VERIFY API =====
@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    uid = str(data.get("user_id"))
    dev = make_hash(data.get("device"))
    ip = get_ip(request)

    if dev in devices or ip in ips:
        return jsonify({"status": "failed"})

    devices[dev] = uid
    ips[ip] = uid
    users[uid] = True

    bot.send_message(uid, "✅ Verification Successful!")

    return jsonify({"status": "success"})

# ===== RUN =====
def run():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run).start()

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
