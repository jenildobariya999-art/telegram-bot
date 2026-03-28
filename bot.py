from flask import Flask, request, jsonify
from telebot import TeleBot, types
import hashlib, json, os, threading

API_TOKEN = os.environ.get("API_TOKEN")
bot = TeleBot(API_TOKEN, parse_mode="HTML")

app = Flask(__name__)

# ===== FILES =====
FILES = ["devices.json", "users.json", "ips.json"]

for f in FILES:
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
ips = load("ips.json")

# ===== HASH =====
def make_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

def get_ip(req):
    return req.headers.get("x-forwarded-for", req.remote_addr)

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.chat.id

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🔐 Verify",
        web_app=types.WebAppInfo("https://verification-beta-five.vercel.app/")
    ))

    bot.send_message(uid, "🔐 Please verify first", reply_markup=markup)

# ===== VERIFY API =====
@app.route("/verify", methods=["POST"])
def verify():
    try:
        data = request.json

        uid = str(data.get("user_id"))
        device_raw = data.get("device")

        if not uid or not device_raw:
            return jsonify({"status": "failed"})

        device = make_hash(device_raw)
        ip = get_ip(request)

        # ❌ Already used
        if device in devices or ip in ips:
            return jsonify({"status": "failed"})

        # ✅ Save
        devices[device] = uid
        ips[ip] = uid
        users[uid] = True

        save("devices.json", devices)
        save("ips.json", ips)
        save("users.json", users)

        # ✅ Send message
        try:
            bot.send_message(uid, "✅ Verification Successful!")
        except:
            pass

        return jsonify({"status": "success"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "failed"})

# ===== RUN =====
def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot).start()

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
