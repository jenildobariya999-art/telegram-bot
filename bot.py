import telebot
from telebot import types
import sqlite3
from flask import Flask, request, jsonify
import threading
import secrets
import requests

TOKEN = "8274297339:AAHfc0y2cXcaOxSFzYNYmY5-oOf2ESIuemg"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

ADMINS = [6925391837, 7528813331]

# ---------- DATABASE ----------
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    ref_by INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0,
    ip TEXT,
    fingerprint TEXT,
    token TEXT
)
""")
conn.commit()

# ---------- FUNCTIONS ----------
def add_user(uid, ref):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, ref_by) VALUES (?,?)", (uid, ref))
        conn.commit()

        if ref != 0 and ref != uid:
            cursor.execute("UPDATE users SET balance = balance + 1 WHERE user_id=?", (ref,))
            conn.commit()

def is_verified(uid):
    cursor.execute("SELECT verified FROM users WHERE user_id=?", (uid,))
    data = cursor.fetchone()
    return data and data[0] == 1

def get_balance(uid):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    data = cursor.fetchone()
    return data[0] if data else 0

# ---------- MENU ----------
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💰 Balance", "👥 Refer")
    return markup

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    args = message.text.split()

    ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
    add_user(uid, ref)

    if not is_verified(uid):
        token = secrets.token_hex(16)

        cursor.execute("UPDATE users SET token=? WHERE user_id=?", (token, uid))
        conn.commit()

        link = f"https://verification-beta-five.vercel.app/?id={uid}&token={token}"

        bot.send_message(uid, f"🔐 Verify here:\n{link}", disable_web_page_preview=True)
        return

    bot.send_message(uid, "✅ Welcome!", reply_markup=main_menu())

# ---------- BALANCE ----------
@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    uid = message.from_user.id
    if not is_verified(uid):
        bot.send_message(uid, "❌ Verify first")
        return
    bot.send_message(uid, f"💰 Balance: ₹{get_balance(uid)}")

# ---------- REFER ----------
@bot.message_handler(func=lambda m: m.text == "👥 Refer")
def refer(message):
    uid = message.from_user.id
    if not is_verified(uid):
        bot.send_message(uid, "❌ Verify first")
        return
    link = f"https://t.me/{bot.get_me().username}?start={uid}"
    bot.send_message(uid, f"👥 Referral Link:\n{link}")

# ---------- ADMIN ----------
@bot.message_handler(commands=['adminpanel'])
def admin(message):
    if message.from_user.id not in ADMINS:
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📢 Broadcast", "➕ Add Balance")
    bot.send_message(message.chat.id, "Admin Panel", reply_markup=markup)

# ---------- VERIFY API ----------
app = Flask(__name__)

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    user_id = int(data.get("user_id"))
    token = data.get("token")
    fingerprint = data.get("fingerprint")

    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # Token check
    cursor.execute("SELECT token FROM users WHERE user_id=?", (user_id,))
    db_token = cursor.fetchone()

    if not db_token or db_token[0] != token:
        return jsonify({"status": "fail", "reason": "Invalid link"})

    # VPN detect
    try:
        vpn = requests.get(f"http://ip-api.com/json/{ip}").json()
        if vpn.get("proxy") or vpn.get("hosting"):
            return jsonify({"status": "fail", "reason": "VPN blocked"})
    except:
        pass

    # Bot detect
    ua = request.headers.get("User-Agent", "").lower()
    if "bot" in ua:
        return jsonify({"status": "fail", "reason": "Bot detected"})

    # Device reuse
    cursor.execute("SELECT user_id FROM users WHERE fingerprint=?", (fingerprint,))
    if cursor.fetchone():
        return jsonify({"status": "fail", "reason": "Device already used"})

    # Save
    cursor.execute("""
    UPDATE users SET verified=1, ip=?, fingerprint=?, token=NULL
    WHERE user_id=?
    """, (ip, fingerprint, user_id))
    conn.commit()

    try:
        bot.send_message(user_id, "✅ Verified Successfully!")
    except:
        pass

    return jsonify({"status": "ok"})

# ---------- RUN ----------
def run_web():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=run_web).start()
    bot.infinity_polling(skip_pending=True)
