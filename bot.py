import telebot
from telebot import types
import sqlite3
import hashlib

BOT_TOKEN = "8608246113:AAEY_ZJ3uyg5p7fQDKdaBD6v1PNGu1hW44E"
ADMIN_ID = 7637137226

bot = telebot.TeleBot(BOT_TOKEN)

def init_db():
    conn = sqlite3.connect('physics_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            student_id TEXT,
            roll_no TEXT,
            username TEXT UNIQUE,
            password TEXT,
            status TEXT DEFAULT 'pending',
            completed_chapters INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            chapter TEXT,
            topic TEXT,
            link TEXT,
            likes INTEGER DEFAULT 0
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM materials")
    if cursor.fetchone()[0] == 0:
        demo_data = [
            ('Bolobidda', 'Chapter 1: Vector', 'Onucched 1.1 (Vector Rashi)', 'https://youtu.be/demo1'),
            ('Bolobidda', 'Chapter 1: Vector', 'Onucched 1.2 (Vector Gunon)', 'https://youtu.be/demo2'),
            ('Tapgodibidda', 'Chapter 1: Temperature', 'Onucched 1.1 (Tap o Tapmatra)', 'https://youtu.be/demo3')
        ]
        cursor.executemany("INSERT INTO materials (subject, chapter, topic, link) VALUES (?, ?, ?, ?)", demo_data)
        conn.commit()
    conn.commit()
    conn.close()

init_db()
user_states = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('physics_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, status FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if user:
        if user[1] == 'approved':
            markup.add("📚 Porashonor Bishoy", "🏆 Leaderboard", "👤 Amar Profile")
            bot.send_message(message.chat.id, f"👋 Swagotom, {user[0]}! Porashona shuru kora jak.", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "⏳ Apnar account ti bortomone Pending ache. Admin allow korle message paben.")
    else:
        markup.add("🔐 Login", "📝 Register")
        bot.send_message(message.chat.id, "🔒 Ei Bot-er materials dekhte hole age account khule login/register korte hobe.", reply_markup=markup)

# --- REGISTRATION PROCESS ---
@bot.message_handler(func=lambda message: message.text == "📝 Register")
def register_start(message):
    user_id = message.from_user.id
    user_states[user_id] = {}
    bot.send_message(message.chat.id, "✍️ Apnar First Name (নামের প্রথম অংশ) দিন:")
    bot.register_next_step_handler(message, reg_first_name)

def reg_first_name(message):
    user_id = message.from_user.id
    user_states[user_id]['first_name'] = message.text.strip()
    bot.send_message(message.chat.id, "✍️ Apnar Last Name (নামের শেষ অংশ) দিন:")
    bot.register_next_step_handler(message, reg_last_name)

def reg_last_name(message):
    user_id = message.from_user.id
    user_states[user_id]['last_name'] = message.text.strip()
    bot.send_message(message.chat.id, "🆔 Apnar Student ID দিন:")
    bot.register_next_step_handler(message, reg_student_id)

def reg_student_id(message):
    user_id = message.from_user.id
    user_states[user_id]['student_id'] = message.text.strip()
    bot.send_message(message.chat.id, "🔢 Apnar Roll Number দিন:")
    bot.register_next_step_handler(message, reg_roll_no)

def reg_roll_no(message):
    user_id = message.from_user.id
    user_states[user_id]['roll_no'] = message.text.strip()
    bot.send_message(message.chat.id, "👤 Ebar ekta unique Username set koren (Jemon: rahim123):")
    bot.register_next_step_handler(message, reg_username)

def reg_username(message):
    user_id = message.from_user.id
    username = message.text.strip()
    
    conn = sqlite3.connect('physics_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    conn.close()
    
    if existing_user:
        bot.send_message(message.chat.id, "❌ Ei username ti use hoye gese. Onyo ekta try koren:")
        bot.register_next_step_handler(message, reg_username)
        return
        
    user_states[user_id]['username'] = username
    bot.send_message(message.chat.id, "🔑 Ebar ekta strong Password set koren:")
    bot.register_next_step_handler(message, reg_password)

def reg_password(message):
    user_id = message.from_user.id
    password = message.text.strip()
    
    if user_id not in user_states:
        bot.send_message(message.chat.id, "⚠️ Error! /start likhe abar shuru koren.")
        return
        
    data = user_states[user_id]
    hashed_pw = hash_password(password)
    
    conn = sqlite3.connect('physics_bot.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (user_id, first_name, last_name, student_id, roll_no, username, password, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (user_id, data['first_name'], data['last_name'], data['student_id'], data['roll_no'], data['username'], hashed_pw))
        conn.commit()
        
        bot.send_message(message.chat.id, "⏳ Registration sfol hoyeche! Eti ekhon Admin Approval-er jonno pending ache. Admin approve korle apnake janano hobe.")
        
        admin_markup = types.InlineKeyboardMarkup()
        admin_markup.add(
            types.InlineKeyboardButton("✅ Accept", callback_data=f"adm_acc_{user_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_{user_id}")
        )
        admin_msg = (
            f"🔔 **New Registration Request!**\n\n"
            f"👤 **Name:** {data['first_name']} {data['last_name']}\n"
            f"🆔 **Student ID:** {data['student_id']}\n"
            f"🔢 **Roll No:** {data['roll_no']}\n"
            f"👤 **Username:** {data['username']}\n"
            f"📱 **Telegram ID:** {user_id}"
        )
        bot.send_message(ADMIN_ID, admin_msg, reply_markup=admin_markup)
        
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Account khola jayni. Abar try koren.")
    finally:
        conn.close()
        if user_id in user_states: del user_states[user_id]

# --- LOGIN PROCESS ---
@bot.message_handler(func=lambda message: message.text == "🔐 Login")
def login_start(message):
    bot.send_message(message.chat.id, "👤 Apnar Username ti likhun:")
    bot.register_next_step_handler(message, login_username)

def login_username(message):
    username = message.text.strip()
    user_id = message.from_user.id
    user_states[user_id] = {'login_user': username}
    bot.send_message(message.chat.id, "🔑 Apnar Password ti likhun:")
    bot.register_next_step_handler(message, login_password)

def login_password(message):
    user_id = message.from_user.id
    password = message.text.strip()
    if user_id not in user_states or 'login_user' not in user_states[user_id]:
        bot.send_message(message.chat.id, "⚠️ Error. Abar try koren.")
        return
        
    username = user_states[user_id]['login_user']
    hashed_pw = hash_password(password)
    
    conn = sqlite3.connect('physics_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, status FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
    user = cursor.fetchone()
    
    if user:
        if user[1] == 'approved':
            cursor.execute("UPDATE users SET user_id = ? WHERE username = ?", (user_id, username))
            conn.commit()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("📚 Porashonor Bishoy", "🏆 Leaderboard", "👤 Amar Profile")
            bot.send_message(message.chat.id, f"🎉 Login successful! Welcome {username}.", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "⏳ Apnar account ti approved na. Admin accept korle login korte parben.")
    else:
        bot.send_message(message.chat.id, "❌ Password bhul ba Username thik nai!")
    
    conn.close()
    if user_id in user_states: del user_states[user_id]

# --- ADMIN ACTIONS ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_callback(call):
    action, target_user_id = call.data.split("_")[1:3]
    target_user_id = int(target_user_id)
    
    conn = sqlite3.connect('physics_bot.db')
    cursor = conn.cursor()
    
    if action == "acc":
        cursor.execute("UPDATE users SET status = 'approved' WHERE user_id = ?", (target_user_id,))
        conn.commit()
        bot.edit_message_text(f"✅ User ID {target_user_id} - ke approval dewa hoyেছে।", call.message.chat.id, call.message.message_id)
        bot.send_message(target_user_id, "🎉 Congratulations! Admin apnar request accept korechen. Ebar `/start` likhe menu open koren.")
    elif action == "rej":
        cursor.execute("DELETE FROM users WHERE user_id = ?", (target_user_id,))
        conn.commit()
        bot.edit_message_text(f"❌ User ID {target_user_id} - er request reject kora hoyeche.", call.message.chat.id, call.message.message_id)
        bot.send_message(target_user_id, "❌ দুঃখিত, অ্যাডমিন আপনার রেজিস্ট্রেশন রিকোয়েস্ট বাতিল করেছেন।")
        
    conn.close()

# --- CONTENT SECTION ---
@bot.message_handler(func=lambda message: message.text == "📚 Porashonor Bishoy")
def show_subjects(message):
    conn = sqlite3.connect('physics_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user or user[0] != 'approved':
        bot.send_message(message.chat.id, "⛔ Please age login/approval nien.")
        conn.close()
        return
    
    cursor.execute("SELECT DISTINCT subject FROM materials")
    subjects = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    for sub in subjects:
        markup.add(types.InlineKeyboardButton(sub[0], callback_data=f"sub_{sub[0]}"))
    bot.send_message(message.chat.id, "📖 Kon bishoyti porte chan?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: not call.data.startswith("adm_"))
def callback_listener(call):
    conn = sqlite3.connect('physics_bot.db')
    cursor = conn.cursor()
    
    if call.data.startswith("sub_"):
        subject = call.data.split("_")[1]
        cursor.execute("SELECT DISTINCT chapter FROM materials WHERE subject = ?", (subject,))
        chapters = cursor.fetchall()
        markup = types.InlineKeyboardMarkup()
        for ch in chapters:
            markup.add(types.InlineKeyboardButton(ch[0], callback_data=f"ch_{subject}_{ch[0]}"))
        bot.edit_message_text(f"📁 {subject} - er chapter gulo:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        
    elif call.data.startswith("ch_"):
        _, subject, chapter = call.data.split("_")
        cursor.execute("SELECT id, topic FROM materials WHERE subject = ? AND chapter = ?", (subject, chapter))
        topics = cursor.fetchall()
        markup = types.InlineKeyboardMarkup()
        for tp in topics:
            markup.add(types.InlineKeyboardButton(tp[1], callback_data=f"tp_{tp[0]}"))
        bot.edit_message_text(f"📑 {chapter} - er onucched gulo:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("tp_"):
        mat_id = call.data.split("_")[1]
        cursor.execute("SELECT subject, chapter, topic, link FROM materials WHERE id = ?", (mat_id,))
        mat = cursor.fetchone()
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎥 Class Video Link", url=mat[3]))
        markup.add(types.InlineKeyboardButton("✅ Pora Shesh (Complete)", callback_data=f"comp_{mat_id}"))
        
        text = f"📚 *Subject:* {mat[0]}\n📖 *Chapter:* {mat[1]}\n📑 *Topic:* {mat[2]}"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
            
    elif call.data.startswith("comp_"):
        user_id = call.from_user.id
        cursor.execute("UPDATE users SET completed_chapters = completed_chapters + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        bot.answer_callback_query(call.id, "🏆 Apnar progress profile-e juktto hoyeche.")
    conn.close()

# --- LEADERBOARD & PROFILE ---
@bot.message_handler(func=lambda message: message.text == "🏆 Leaderboard")
def show_leaderboard(message):
    conn = sqlite3.connect('physics_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name, completed_chapters FROM users WHERE status='approved' ORDER BY completed_chapters DESC LIMIT 5")
    leaders = cursor.fetchall()
    conn.close()
    text = "🏆 **Top 5 Porishromi Chatro (Leaderboard)** 🏆\n\n"
    for i, leader in enumerate(leaders, 1):
        text += f"{i}. 👤 {leader[0]} {leader[1]} — {leader[2]} ti onucched shesh koreche.\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👤 Amar Profile")
def show_profile(message):
    conn = sqlite3.connect('physics_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name, student_id, roll_no, username, completed_chapters FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        text = (
            f"👤 **Profile Details**\n\n"
            f"📛 **Name:** {user[0]} {user[1]}\n"
            f"🆔 **Student ID:** {user[2]}\n"
            f"🔢 **Roll No:** {user[3]}\n"
            f"👤 **Username:** {user[4]}\n"
            f"📊 ** Study Complete :** {user[5]} ti"
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

print("🤖 Bot Running Successfully...")
bot.infinity_polling()
