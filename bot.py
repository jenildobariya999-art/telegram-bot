from flask import Flask, request, jsonify
from flask_cors import CORS
from telebot import TeleBot, types
import hashlib, sqlite3, os, threading, time, shutil

# ===== CONFIG =====
API_TOKEN = os.environ.get("API_TOKEN")
DOMAIN = "https://verification-beta-five.vercel.app"

ADMIN_IDS = ["6925391837", "7528813331"]
bot_status = True

# ===== BOT =====
bot = TeleBot(API_TOKEN, parse_mode="HTML")
bot.remove_webhook()

app = Flask(__name__)
CORS(app)

# ===== DATABASE =====
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (id TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS balance (id TEXT, amount REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS devices (hash TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS ips (ip TEXT)")
conn.commit()

# ===== HELPERS =====
def is_admin(uid):
    return str(uid) in ADMIN_IDS

def make_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

def get_ip(req):
    if req.headers.get("X-Forwarded-For"):
        return req.headers.get("X-Forwarded-For").split(",")[0]
    return req.remote_addr

# ===== DB FUNCTIONS =====
def add_user(uid):
    cursor.execute("INSERT INTO users VALUES (?)", (uid,))
    conn.commit()

def is_user(uid):
    cursor.execute("SELECT * FROM users WHERE id=?", (uid,))
    return cursor.fetchone() is not None

def add_balance(uid, amt):
    cursor.execute("SELECT * FROM balance WHERE id=?", (uid,))
    if cursor.fetchone():
        cursor.execute("UPDATE balance SET amount = amount + ? WHERE id=?", (amt, uid))
    else:
        cursor.execute("INSERT INTO balance VALUES (?,?)", (uid, amt))
    conn.commit()

def get_balance(uid):
    cursor.execute("SELECT amount FROM balance WHERE id=?", (uid,))
    row = cursor.fetchone()
    return row[0] if row else 0

def device_used(dev):
    cursor.execute("SELECT * FROM devices WHERE hash=?", (dev,))
    return cursor.fetchone()

def ip_used(ip):
    cursor.execute("SELECT * FROM ips WHERE ip=?", (ip,))
    return cursor.fetchone()

def save_device(dev):
    cursor.execute("INSERT INTO devices VALUES (?)", (dev,))
    conn.commit()

def save_ip(ip):
    cursor.execute("INSERT INTO ips VALUES (?)", (ip,))
    conn.commit()

# ===== HOME =====
@app.route("/")
def home():
    return "Bot Running ✅"

# ===== MENU =====
def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("💰 Balance", "📊 Info")
    return m

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    if not bot_status:
        return

    uid = str(msg.chat.id)

    if is_user(uid):
        bot.send_message(uid, "🏠 <b>Welcome Back</b>", reply_markup=menu())
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔐 Verify", web_app=types.WebAppInfo(DOMAIN)))
        bot.send_message(uid, "🛡 <b>Verify first</b>", reply_markup=markup)

# ===== BUTTONS =====
@bot.message_handler(func=lambda m: True)
def buttons(msg):
    uid = str(msg.chat.id)

    if msg.text == "💰 Balance":
        bot.send_message(uid, f"💰 ₹{get_balance(uid)}")

    elif msg.text == "📊 Info":
        bot.send_message(uid, f"🆔 {uid}")

# ===== VERIFY =====
@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    uid = str(data.get("user_id"))

    device_data = data.get("device") + get_ip(request) + request.headers.get("User-Agent", "")
    dev = make_hash(device_data)
    ip = get_ip(request)

    if device_used(dev) or ip_used(ip):
        return jsonify({"status": "failed"})

    save_device(dev)
    save_ip(ip)
    add_user(uid)

    bot.send_message(uid, "✅ Verified!", reply_markup=menu())
    return jsonify({"status": "success"})

# ===== ADMIN =====
@bot.message_handler(commands=['adminpanel'])
def adminpanel(msg):
    if not is_admin(msg.chat.id):
        return

    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("💰 Add Balance", callback_data="bal"))
    m.add(types.InlineKeyboardButton("📢 Broadcast", callback_data="bc"))

    bot.send_message(msg.chat.id, "Admin Panel", reply_markup=m)

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid = str(call.from_user.id)

    if not is_admin(uid):
        return

    if call.data == "bal":
        msg = bot.send_message(uid, "user_id amount")
        bot.register_next_step_handler(msg, addbal)

    elif call.data == "bc":
        msg = bot.send_message(uid, "Send msg")
        bot.register_next_step_handler(msg, broadcast)

def addbal(msg):
    uid, amt = msg.text.split()
    add_balance(uid, float(amt))
    bot.send_message(msg.chat.id, "Done")

def broadcast(msg):
    cursor.execute("SELECT id FROM users")
    for u in cursor.fetchall():
        try:
            bot.send_message(u[0], msg.text)
        except:
            pass

# ===== BACKUP =====
def backup():
    while True:
        time.sleep(3600)
        shutil.copy("data.db", "backup.db")
        print("Backup done")

threading.Thread(target=backup).start()

# ===== DOWNLOAD BACKUP =====
@bot.message_handler(commands=['backup'])
def send_backup(msg):
    if not is_admin(msg.chat.id):
        return

    with open("backup.db", "rb") as f:
        bot.send_document(msg.chat.id, f)

# ===== RUN =====
def run():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run).start()

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
