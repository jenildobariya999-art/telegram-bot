import telebot
from telebot import types
import sqlite3
import time

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
    ref_by INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

conn.commit()

# ---------------- DEFAULT TEXTS ----------------
def get_text(key, default):
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    data = cursor.fetchone()
    return data[0] if data else default

def set_text(key, value):
    cursor.execute("REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
    conn.commit()

# Default messages
if not get_text("welcome"):
    set_text("welcome", "👋 Welcome! Use menu below")
if not get_text("refer"):
    set_text("refer", "👥 Your Referral Link:\n{link}")

# ---------------- USER FUNCTIONS ----------------
def add_user(uid, ref):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, ref_by) VALUES (?,?)", (uid, ref))
        conn.commit()

        if ref != 0 and ref != uid:
            cursor.execute("UPDATE users SET balance = balance + 1 WHERE user_id=?", (ref,))
            conn.commit()

def get_balance(uid):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    data = cursor.fetchone()
    return data[0] if data else 0

# ---------------- KEYBOARD ----------------
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💰 Balance", "👥 Refer")
    markup.row("ℹ️ Info")
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

    text = get_text("welcome")
    bot.send_message(uid, text, reply_markup=main_menu())

# ---------------- BALANCE ----------------
@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    bal = get_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"💰 Your Balance: ₹{bal}")

# ---------------- REFER ----------------
@bot.message_handler(func=lambda m: m.text == "👥 Refer")
def refer(message):
    uid = message.from_user.id
    link = f"https://t.me/{bot.get_me().username}?start={uid}"
    text = get_text("refer").format(link=link)
    bot.send_message(uid, text)

# ---------------- ADMIN PANEL ----------------
@bot.message_handler(commands=['adminpanel'])
def admin_panel(message):
    if message.from_user.id not in ADMINS:
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📢 Broadcast", "➕ Add Balance")
    markup.row("🔄 Reset User", "✏️ Set Text")
    markup.row("⬅️ Back")

    bot.send_message(message.chat.id, "⚙️ Admin Panel", reply_markup=markup)

# ---------------- BACK ----------------
@bot.message_handler(func=lambda m: m.text == "⬅️ Back")
def back(message):
    bot.send_message(message.chat.id, "Back to menu", reply_markup=main_menu())

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
        bot.send_message(message.chat.id, "✅ Balance added")
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
        bot.send_message(message.chat.id, "✅ Reset done")
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

    bot.send_message(message.chat.id, "✅ Broadcast done")

# ---------------- SET TEXT ----------------
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
        bot.send_message(message.chat.id, "✅ Updated")
    except:
        bot.send_message(message.chat.id, "❌ Error")

# ---------------- RUN ----------------
if __name__ == "__main__":
    print("Bot running...")

    try:
        bot.remove_webhook()
    except:
        pass

    bot.infinity_polling(skip_pending=True)
