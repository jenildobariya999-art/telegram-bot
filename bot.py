from flask import Flask, request, jsonify
from flask_cors import CORS
from telebot import TeleBot, types
import hashlib, json, os, threading, requests

# ===== CONFIG =====
API_TOKEN = os.environ.get("API_TOKEN")
DOMAIN = "https://verification-beta-five.vercel.app"

bot = TeleBot(API_TOKEN, parse_mode="HTML")

# FIX 409 ERROR
bot.remove_webhook()
bot.delete_webhook()

app = Flask(__name__)
CORS(app)

# ===== FILES =====
FILES = {
    "devices": "devices.json",
    "users": "users.json",
    "failed": "failed.json",
    "ips": "ips.json"
}

for f in FILES.values():
    if not os.path.exists(f):
        with open(f, "w") as x:
            json.dump({}, x)

def load(f):
    try:
        return json.load(open(f))
    except:
        return {}

def save(name, data):
    json.dump(data, open(FILES[name], "w"))

devices = load(FILES["devices"])
users = load(FILES["users"])
failed = load(FILES["failed"])
ips = load(FILES["ips"])

# ===== HELPERS =====
def hash_device(data):
    return hashlib.sha256(data.encode()).hexdigest()

def get_ip(req):
    return req.headers.get("X-Forwarded-For", req.remote_addr)

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.chat.id)

    if uid in users:
        return bot.send_message(uid, "✅ Already Verified")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🔐 Verify Device",
        web_app=types.WebAppInfo(DOMAIN)
    ))

    bot.send_message(uid, "🛡 Click below to verify", reply_markup=markup)

# ===== VERIFY API =====
@app.route("/verify", methods=["POST"])
def verify():
    data = request.json

    uid = str(data.get("user_id"))
    device_raw = data.get("device")
    ip = get_ip(request)

    device_hash = hash_device(device_raw)

    # 🌍 VPN CHECK
    try:
        ipinfo = requests.get(f"https://ipapi.co/{ip}/json").json()
        if ipinfo.get("proxy"):
            return jsonify({"status": "failed", "reason": "VPN"})
    except:
        pass

    # 📵 Emulator detect
    if "sdk_gphone" in device_raw or "Emulator" in device_raw:
        return jsonify({"status": "failed", "reason": "Emulator"})

    # 🤖 Bot detect
    if "Headless" in device_raw or "bot" in device_raw.lower():
        return jsonify({"status": "failed", "reason": "Bot"})

    # 🔒 One device + IP
    if device_hash in devices or ip in ips:
        failed[uid] = True
        save("failed", failed)
        return jsonify({"status": "failed"})

    # SAVE
    devices[device_hash] = uid
    ips[ip] = uid
    users[uid] = True

    save("devices", devices)
    save("ips", ips)
    save("users", users)

    bot.send_message(uid, "✅ Verification Successful!")

    return jsonify({"status": "success"})

# ===== RUN =====
def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot).start()

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
