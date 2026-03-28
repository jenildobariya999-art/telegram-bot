from flask import Flask, request, jsonify
from telebot import TeleBot, types
import hashlib, json, os, threading

API_TOKEN = os.environ.get("API_TOKEN")

bot = TeleBot(API_TOKEN, parse_mode="HTML")
bot.remove_webhook()

app = Flask(__name__)

# ===== FILE =====
DATA_FILE = "data.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": {}, "devices": {}, "ips": {}}, f)

def load():
    with open(DATA_FILE) as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def make_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

def get_ip(req):
    return req.headers.get("X-Forwarded-For", req.remote_addr)

# ===== TELEGRAM START =====
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.chat.id

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "🔐 Verify",
            web_app=types.WebAppInfo("https://verification-beta-five.vercel.app/")
        )
    )

    bot.send_message(uid, "🛡 Please verify first", reply_markup=markup)

# ===== VERIFY API =====
@app.route("/verify", methods=["POST"])
def verify():
    try:
        data = request.json
        uid = str(data.get("user_id"))
        device = make_hash(data.get("device"))
        ip = get_ip(request)

        db = load()

        if device in db["devices"] or ip in db["ips"]:
            return jsonify({"status": "failed"})

        db["devices"][device] = uid
        db["ips"][ip] = uid
        db["users"][uid] = True

        save(db)

        bot.send_message(uid, "✅ Verified Successfully!")

        return jsonify({"status": "success"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error"})

# ===== RUN =====
def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot).start()

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
