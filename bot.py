import telebot
from telebot import types
import sqlite3
from flask import Flask, request, jsonify
import threading

TOKEN = "8274297339:AAHfc0y2cXcaOxSFzYNYmY5-oOf2ESIuemg"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

ADMINS = [6925391837, 7528813331]

# ---------------- DATABASE ----------------
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    ref_by INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0
)
""")
conn.commit()

# ---------------- FUNCTIONS ----------------
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

def set_verified(uid):
    cursor.execute("UPDATE users SET verified=1 WHERE user_id=?", (uid,))
    conn.commit()

def get_balance(uid):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    data = cursor.fetchone()
    return data[0] if data else 0

# ---------------- KEYBOARD ----------------
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💰 Balance", "👥 Refer")
    return markup

# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    args = message.text.split()

    ref = 0
    if len(args) > 1:
        try:
            ref = int(args[1])
        except:
            ref = 0

    add_user(uid, ref)

    if not is_verified(uid):
        verify_link = f"https://verification-beta-five.vercel.app/?id={uid}"
        bot.send_message(uid,
            f"🔐 Please verify first:\n{verify_link}",
            disable_web_page_preview=True
        )
        return

    bot.send_message(uid, "✅ Welcome!", reply_markup=main_menu())

# ---------------- BALANCE ----------------
@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    uid = message.from_user.id

    if not is_verified(uid):
        bot.send_message(uid, "❌ Verify first using /start")
        return

    bot.send_message(uid, f"💰 Balance: ₹{get_balance(uid)}")

# ---------------- REFER ----------------
@bot.message_handler(func=lambda m: m.text == "👥 Refer")
def refer(message):
    uid = message.from_user.id

    if not is_verified(uid):
        bot.send_message(uid, "❌ Verify first using /start")
        return

    link = f"https://t.me/{bot.get_me().username}?start={uid}"
    bot.send_message(uid, f"👥 Your Referral Link:\n{link}")

# ---------------- ADMIN PANEL ----------------
@bot.message_handler(commands=['adminpanel'])
def admin_panel(message):
    if message.from_user.id not in ADMINS:
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📢 Broadcast", "➕ Add Balance")
    markup.row("🔄 Reset User", "⬅️ Back")

    bot.send_message(message.chat.id, "⚙️ Admin Panel", reply_markup=markup)

# ---------------- BACK ----------------
@bot.message_handler(func=lambda m: m.text == "⬅️ Back")
def back(message):
    bot.send_message(message.chat.id, "Main Menu", reply_markup=main_menu())

# ---------------- ADD BALANCE ----------------
@bot.message_handler(func=lambda m: m.text == "➕ Add Balance")
def add_balance(message):
    if message.from_user.id not in ADMINS:
        return

    msg = bot.send_message(message.chat.id, "Send: user_id amount")
    bot.register_next_step_handler(msg, process_add_balance)

def process_add_balance(message):
    try:
        uid, amt = message.text.split()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (float(amt), int(uid)))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Balance Added")
    except:
        bot.send_message(message.chat.id, "❌ Error")

# ---------------- RESET USER ----------------
@bot.message_handler(func=lambda m: m.text == "🔄 Reset User")
def reset_user(message):
    if message.from_user.id not in ADMINS:
        return

    msg = bot.send_message(message.chat.id, "Send user_id")
    bot.register_next_step_handler(msg, process_reset)

def process_reset(message):
    try:
        uid = int(message.text)
        cursor.execute("DELETE FROM users WHERE user_id=?", (uid,))
        conn.commit()
        bot.send_message(message.chat.id, "✅ User Reset")
    except:
        bot.send_message(message.chat.id, "❌ Error")

# ---------------- BROADCAST ----------------
@bot.message_handler(func=lambda m: m.text == "📢 Broadcast")
def broadcast(message):
    if message.from_user.id not in ADMINS:
        return

    msg = bot.send_message(message.chat.id, "Send message")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    for u in users:
        try:
            bot.send_message(u[0], message.text)
        except:
            pass

    bot.send_message(message.chat.id, "✅ Broadcast Done")

# ---------------- FLASK VERIFY API ----------------
app = Flask(__name__)

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    user_id = int(data.get("user_id"))

    set_verified(user_id)

    try:
        bot.send_message(user_id, "✅ Verification Successful! Now use /start")
    except:
        pass

    return jsonify({"status": "ok"})

# ---------------- RUN BOTH ----------------
def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    print("Bot + Web running...")

    try:
        bot.remove_webhook()
    except:
        pass

    threading.Thread(target=run_flask).start()
    bot.infinity_polling(skip_pending=True)
