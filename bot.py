from flask import Flask, request, jsonify
from telebot import TeleBot, types
import hashlib, threading, os

# ===== CONFIG =====
API_TOKEN = os.environ.get("API_TOKEN")
DOMAIN = "https://verification-beta-five.vercel.app"

bot = TeleBot(API_TOKEN, parse_mode="HTML")
bot.remove_webhook()

app = Flask(__name__)

# ===== MEMORY STORAGE (NO JSON / NO DB) =====
users = {}
devices = set()
ips = set()

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

    bot.send_message(uid, "🛡 Click below to verify", reply_markup=markup)

# ===== VERIFY API =====
@app.route("/verify", methods=["POST"])
def verify():
    data = request.json

    if not data:
        return jsonify({"status": "error"})

    uid = str(data.get("user_id"))
    device_raw = data.get("device")

    if not uid or not device_raw:
        return jsonify({"status": "error"})

    dev = make_hash(device_raw)
    ip = get_ip(request)

    # 🚫 Already used
    if dev in devices or ip in ips:
        return jsonify({"status": "failed"})

    # ✅ Save
    devices.add(dev)
    ips.add(ip)
    users[uid] = True

    try:
        bot.send_message(uid, "✅ Verification Successful!")
    except:
        pass

    return jsonify({"status": "success"})

# ===== RUN BOT =====
def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot).start()

# ===== RUN SERVER =====
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
