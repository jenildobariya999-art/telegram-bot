from flask import Flask, request, jsonify
from telebot import TeleBot, types
import hashlib, threading, os, time

API_TOKEN = os.environ.get("API_TOKEN")
DOMAIN = "https://verification-beta-five.vercel.app"

bot = TeleBot(API_TOKEN, parse_mode="HTML")

# 🚀 IMPORTANT FIX
bot.remove_webhook()
time.sleep(1)

app = Flask(__name__)

users = {}
devices = set()
ips = set()

@app.route("/")
def home():
    return "Bot Running ✅"

def make_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

def get_ip(req):
    if req.headers.get("X-Forwarded-For"):
        return req.headers.get("X-Forwarded-For").split(",")[0]
    return req.remote_addr

@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.chat.id)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔐 Verify", web_app=types.WebAppInfo(DOMAIN)))

    bot.send_message(uid, "Click to verify", reply_markup=markup)

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json

    uid = str(data.get("user_id"))
    dev = make_hash(data.get("device"))
    ip = get_ip(request)

    if dev in devices or ip in ips:
        return jsonify({"status": "failed"})

    devices.add(dev)
    ips.add(ip)
    users[uid] = True

    try:
        bot.send_message(uid, "✅ Verified Successfully")
    except:
        pass

    return jsonify({"status": "success"})

def run_bot():
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print("Restarting bot...", e)
            time.sleep(3)

threading.Thread(target=run_bot).start()

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
