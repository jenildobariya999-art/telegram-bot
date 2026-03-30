from flask import Flask, request, jsonify
from flask_cors import CORS
from telebot import TeleBot, types
import hashlib, json, os, threading

# ===== CONFIG =====
API_TOKEN = os.environ.get("API_TOKEN")
DOMAIN = "https://verification-beta-five.vercel.app"  # tera webapp

ADMIN_IDS = ["6925391837", "7528813331"]

# ===== INIT =====
bot = TeleBot(API_TOKEN, parse_mode="HTML")
bot.remove_webhook()

app = Flask(__name__)
CORS(app)

# ===== FILES =====
FILES = {
    "devices": "devices.json",
    "users": "users.json",
    "failed": "failed.json",
}

# create files
for f in FILES.values():
    if not os.path.exists(f):
        with open(f, "w") as file:
            json.dump({}, file)

def load(file):
    try:
        with open(file) as f:
            return json.load(f)
    except:
        return {}

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

devices = load(FILES["devices"])
users = load(FILES["users"])
failed = load(FILES["failed"])

# ===== HELPERS =====
def make_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

# ===== HOME =====
@app.route("/")
def home():
    return "Bot Running ✅"

# ===== MENU =====
def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("💰 Balance", "👥 Refer")
    return m

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.chat.id)

    if uid in users:
        bot.send_message(uid, "🏠 <b>Welcome Back!</b>", reply_markup=main_menu())
        return

    if uid in failed:
        bot.send_message(uid, "❌ <b>Verification Failed</b>")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔐 Verify", web_app=types.WebAppInfo(DOMAIN)))

    bot.send_message(uid, "🛡 <b>Please verify first</b>", reply_markup=markup)

# ===== VERIFY API =====
@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    uid = str(data.get("user_id"))
    dev = make_hash(data.get("device"))

    # ❌ same device used by another account
    if dev in devices:
        if devices[dev] != uid:
            failed[uid] = True
            save(FILES["failed"], failed)
            return jsonify({"status": "failed"})
        else:
            return jsonify({"status": "success"})

    # ✅ new device
    devices[dev] = uid
    users[uid] = True

    save(FILES["devices"], devices)
    save(FILES["users"], users)

    bot.send_message(uid, "✅ <b>Verified Successfully!</b>", reply_markup=main_menu())

    return jsonify({"status": "success"})

# ===== RUN BOT (FIX 409 ERROR) =====
def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot).start()

# ===== RUN FLASK =====
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
