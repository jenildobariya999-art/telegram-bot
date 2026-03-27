import telebot
from flask import Flask, request, jsonify, send_file
import sqlite3, threading, time, shutil, os

API_TOKEN = os.getenv("API_TOKEN")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# ---------- DATABASE ----------
def db():
    return sqlite3.connect("data.db", check_same_thread=False)

conn = db()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
verified INTEGER DEFAULT 0,
device TEXT,
balance INTEGER DEFAULT 0
)
""")
conn.commit()

# ---------- BACKUP ----------
def backup():
    while True:
        time.sleep(3600)
        shutil.copy("data.db","backup.db")

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

    cur.execute("SELECT device, verified FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()

    if row:
        saved_device, verified = row

        # Same device → allow
        if saved_device == device:
            cur.execute("UPDATE users SET verified=1 WHERE user_id=?", (uid,))
            conn.commit()
            bot.send_message(uid, "✅ Verified Successfully!")
            return jsonify({"status":"success"})

        # New device → fail
        else:
            bot.send_message(uid, "❌ Verification Failed!\nMultiple device detected")
            return jsonify({"status":"failed"})

    else:
        # New user
        cur.execute("INSERT INTO users(user_id, device, verified) VALUES(?,?,1)",
                    (uid, device))
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
        bot.send_message(uid, "🎉 Welcome Back! Already Verified")
    else:
        link = f"https://web-production-0df8e.up.railway.app/?uid={uid}"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔐 Verify", url=link))
        bot.send_message(uid, "⚠️ Please verify your device", reply_markup=markup)

# ---------- RUN ----------
def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
