from flask import Flask, request, jsonify
from telebot import TeleBot, types
import hashlib, os, threading, time

API_TOKEN = os.environ.get("API_TOKEN")
DOMAIN = "https://verification-beta-five.vercel.app"

bot = TeleBot(API_TOKEN)

# ❌ 409 FIX
try:
    bot.remove_webhook()
except:
    pass

app = Flask(__name__)

devices = set()
ips = set()

def make_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

def get_ip(req):
    if req.headers.get("X-Forwarded-For"):
        return req.headers.get("X-Forwarded-For").split(",")[0]
    return req.remote_addr

@app.route("/")
def home():
    return "OK"

@bot.message_handler(commands=['start'])
def start(msg):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🔐 Verify",
        web_app=types.WebAppInfo(DOMAIN)
    ))
    bot.send_message(msg.chat.id, "Click Verify", reply_markup=markup)

@app.route("/verify", methods=["POST"])
def verify():
    try:
        data = request.json

        uid = str(data.get("user_id"))
        device_raw = data.get("device")

        if not uid or not device_raw:
            return jsonify({"status": "error"})

        dev = make_hash(device_raw)
        ip = get_ip(request)

        if dev in devices or ip in ips:
            return jsonify({"status": "failed"})

        devices.add(dev)
        ips.add(ip)

        try:
            bot.send_message(uid, "✅ Verified Successfully")
        except:
            pass

        return jsonify({"status": "success"})

    except Exception as e:
        print("VERIFY ERROR:", e)
        return jsonify({"status": "error"})

def run_bot():
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print("BOT ERROR:", e)
            time.sleep(5)

threading.Thread(target=run_bot).start()

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
