# bot.py
import os
import telebot
from telebot import types
import sqlite3
import threading
from flask import Flask

# ---------------- TOKEN ----------------
TOKEN = os.environ.get("BOT_TOKEN")  # Set this in Railway Environment Variables
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ---------------- ADMINS ----------------
ADMINS = [6925391837, 7528813331]

# ---------------- DATABASE ----------------
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    ref_by INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0
)
""")

# Settings table
cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")
conn.commit()

# ---------------- DEFAULT TEXTS ----------------
def get_text(key, default=""):
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    data = cursor.fetchone()
    return data[0] if data else default

def set_text(key, value):
    cursor.execute("REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
    conn.commit()

# Set defaults
if not get_text("welcome"):
    set_text("welcome", "👋 Welcome! Please verify yourself using /verify")
if not get_text("refer"):
    set_text("refer", "👥 Your Referral Link:\n{link}")

# ---------------- USER FUNCTIONS ----------------
def add_user(uid, ref):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, ref_by) VALUES (?,?)", (uid, ref))
        conn.commit()
        # Add referral bonus if valid
        if ref != 0 and ref != uid:
            cursor.execute("SELECT * FROM users WHERE user_id=?", (ref,))
            if cursor.fetchone():
                cursor.execute("UPDATE users SET balance = balance + 1 WHERE user_id=?", (ref,))
                conn.commit()

def get_balance(uid):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    data = cursor.fetchone()
    return data[0] if data else 0

def is_verified(uid):
    cursor.execute("SELECT verified FROM users WHERE user_id=?", (uid,))
    data = cursor.fetchone()
    return data[0] == 1 if data else False

def set_verified(uid):
    cursor.execute("UPDATE users SET verified = 1 WHERE user_id=?", (uid,))
    conn.commit()

# ---------------- KEYBOARDS ----------------
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💰 Balance", "👥 Refer")
    markup.row("ℹ️ Info")
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📢 Broadcast", "➕ Add Balance")
    markup.row("🔄 Reset User", "✏️ Set Text")
    markup.row("⬅️ Back")
    return markup

# ---------------- BOT HANDLERS ----------------

# Start / Referral
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
        bot.send_message(uid, "👋 Please verify yourself using /verify")
    else:
        bot.send_message(uid, get_text("welcome"), reply_markup=main_menu())

# Verification
@bot.message_handler(commands=['verify'])
def verify(message):
    uid = message.from_user.id
    add_user(uid, 0)
    set_verified(uid)
    bot.send_message(uid, "✅ You are verified! Use the menu below.", reply_markup=main_menu())

# Balance
@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    uid = message.from_user.id
    if not is_verified(uid):
        bot.send_message(uid.chat.id, "❌ Please verify using /verify first")
        return
    bot.send_message(message.chat.id, f"💰 Your Balance: ₹{get_balance(uid)}")

# Refer
@bot.message_handler(func=lambda m: m.text == "👥 Refer")
def refer(message):
    uid = message.from_user.id
    if not is_verified(uid):
        bot.send_message(message.chat.id, "❌ Please verify using /verify first")
        return
    link = f"https://t.me/{bot.get_me().username}?start={uid}"
    bot.send_message(uid, get_text("refer").format(link=link))

# Info
@bot.message_handler(func=lambda m: m.text == "ℹ️ Info")
def info(message):
    bot.send_message(message.chat.id, "This is a referral bot demo. ✅")

# Admin panel
@bot.message_handler(commands=['adminpanel'])
def admin_panel(message):
    if message.from_user.id not in ADMINS:
        return
    bot.send_message(message.chat.id, "⚙️ Admin Panel", reply_markup=admin_menu())

# Back
@bot.message_handler(func=lambda m: m.text == "⬅️ Back")
def back(message):
    bot.send_message(message.chat.id, "Back to main menu", reply_markup=main_menu())

# Add Balance
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
        bot.send_message(message.chat.id, "✅ Balance added")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

# Reset User
@bot.message_handler(func=lambda m: m.text == "🔄 Reset User")
def reset_user(message):
    if message.from_user.id not in ADMINS:
        return
    msg = bot.send_message(message.chat.id, "Send user_id")
    bot.register_next_step_handler(msg, process_reset_user)

def process_reset_user(message):
    try:
        uid = int(message.text)
        cursor.execute("DELETE FROM users WHERE user_id=?", (uid,))
        conn.commit()
        bot.send_message(message.chat.id, "✅ User reset")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

# Broadcast
@bot.message_handler(func=lambda m: m.text == "📢 Broadcast")
def broadcast(message):
    if message.from_user.id not in ADMINS:
        return
    msg = bot.send_message(message.chat.id, "Send message to broadcast")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    for u in users:
        try:
            bot.send_message(u[0], message.text)
        except:
            pass
    bot.send_message(message.chat.id, "✅ Broadcast done")

# Set Text
@bot.message_handler(func=lambda m: m.text == "✏️ Set Text")
def set_text_cmd(message):
    if message.from_user.id not in ADMINS:
        return
    msg = bot.send_message(message.chat.id, "Send: key | text")
    bot.register_next_step_handler(msg, process_set_text)

def process_set_text(message):
    try:
        key, value = message.text.split("|", 1)
        set_text(key.strip(), value.strip())
        bot.send_message(message.chat.id, "✅ Text updated")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

# ---------------- FLASK KEEP-ALIVE ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ---------------- RUN BOT ----------------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot is running...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
