import telebot
from flask import Flask, request, jsonify, send_file
import sqlite3, threading, time, shutil, os

API_TOKEN = os.getenv("API_TOKEN")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# ---------- DATABASE ----------
conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
device TEXT,
ip TEXT,
verified INTEGER DEFAULT 0
)
""")
conn.commit()

# ---------- BACKUP ----------
def backup():
    while True:
        time.sleep(3600)
        shutil.copy("data.db", "backup.db")

threading.Thread(target=backup, daemon=True).start()

# ---------- WEBSITE ----------
@app.route("/")
def home():
    return send_file("index.html")

# ---------- VERIFY API ----------
@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    uid = int(data.get("user_id"))
    device = data.get("device")

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ua = request.headers.get("User-Agent", "").lower()

    # 🚫 Fake browser block
    blocked = ["python", "curl", "wget", "bot", "spider"]
    if any(x in ua for x in blocked):
        return jsonify({"status":"failed"})

    # 🚫 Basic VPN/local IP block
    if ip.startswith("10.") or ip.startswith("192.168"):
        return jsonify({"status":"failed"})

    # 🔍 Already verified
    cur.execute("SELECT verified FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()

    if row and row[0] == 1:
        return jsonify({"status":"failed"})

    # 🚫 Device already used
    cur.execute("SELECT user_id FROM users WHERE device=?", (device,))
    if cur.fetchone():
        return jsonify({"status":"failed"})

    # 🚫 IP already used
    cur.execute("SELECT user_id FROM users WHERE ip=?", (ip,))
    if cur.fetchone():
        return jsonify({"status":"failed"})

    # ✅ Save user
    cur.execute("INSERT OR REPLACE INTO users(user_id, device, ip, verified) VALUES(?,?,?,1)",
                (uid, device, ip))
    conn.commit()

    bot.send_message(uid, "✅ Verified Successfully!")
    return jsonify({"status":"success"})

# ---------- BOT ----------
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.chat.id

    cur.execute("SELECT verified FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()

    if row and row[0] == 1:
        bot.send_message(uid, "🎉 Already Verified!")
    else:
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

        link = f"https://web-production-0df8e.up.railway.app/?uid={uid}"

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                "🔐 Verify",
                web_app=WebAppInfo(url=link)
            )
        )

        bot.send_message(uid, "🔒 Verify yourself to continue", reply_markup=markup)

# ---------- RUN ----------
def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
