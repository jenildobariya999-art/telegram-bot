from flask import Flask, request, jsonify
from telebot import TeleBot, types
import hashlib, json, os, threading

API_TOKEN = os.environ.get("API_TOKEN")

bot = TeleBot(API_TOKEN, parse_mode="HTML")

# 🔥 IMPORTANT FIX
bot.remove_webhook()

app = Flask(__name__)

# ===== FILES =====
FILES = {
    "devices": "devices.json",
    "users": "users.json",
    "failed": "failed.json",
    "ips": "ips.json"
}

# create files
for f in FILES.values():
    if not os.path.exists(f):
        with open(f, "w") as file:
            json.dump({}, file)

def load(file):
    with open(file) as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

devices = load("devices.json")
users = load("users.json")
failed = load("failed.json")
ips = load("ips.json")

# ===== HELPERS =====
def make_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

def get_ip(req):
    if req.headers.get("X-Forwarded-For"):
        return req.headers.get("X-Forwarded-For").split(",")[0]
    return req.remote_addr

# ===== HOME =====
@app.route("/")
def home():
    return "Bot Running ✅"

# ===== MENU =====
def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("✅ Verified")
    return m

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.chat.id)

    if uid in users:
        bot.send_message(uid, "✅ Already Verified", reply_markup=menu())
        return

    if uid in failed:
        bot.send_message(uid, "❌ Already Used Device/IP")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🔐 Verify",
        web_app=types.WebAppInfo("https://verification-beta-five.vercel.app/")
    ))

    bot.send_message(uid, "Click below to verify", reply_markup=markup)

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
            save("failed.json", failed)
            return jsonify({"status": "failed"})

        devices[dev] = uid
        ips[ip] = uid
        users[uid] = True

        save("devices.json", devices)
        save("ips.json", ips)
        save("users.json", users)

        bot.send_message(uid, "✅ Verified Successfully!", reply_markup=menu())

        return jsonify({"status": "success"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error"})

# ===== BOT RUN =====
def run_bot():
    print("Bot started...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
