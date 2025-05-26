import time
import json
import os
import threading
from telebot import TeleBot, types

# === BOT SETUP ===
API_TOKEN = '7776105510:AAGdP9dkhearJbMn-6-3REN4u_DiNZ6FGDk' 
ADMIN_ID = 8196698715  
ROYAL_MAIL_TRACKING_URL = "https://www.royalmail.com/track-your-item"

bot = TeleBot(API_TOKEN)

# === SESSION & DATA ===
sessions = {}
user_db = {}
tracking_data = {}

# Load user database (simulate from file)
if os.path.exists("user_data.json"):
    with open("user_data.json", "r") as f:
        user_db = json.load(f)

# Load tracking data (simulate from file)
if os.path.exists("tracking.json"):
    with open("tracking.json", "r") as f:
        tracking_data = json.load(f)

# === TRACKING HANDLER ===
@bot.message_handler(func=lambda m: m.text == "📦 Track")
def handle_tracking_request(m):
    step = sessions.get(m.chat.id, {}).get("step")
    if step in ["awaiting_code", "awaiting_bank_screenshot", "awaiting_receipt_photo"]:
        bot.send_message(m.chat.id, "\u26a0\ufe0f You're in a payment process. Please upload your proof and type *paid*.\nUse /start to cancel.", parse_mode="Markdown")
        return

    sessions[m.chat.id] = {"step": "awaiting_postcode"}
    bot.send_message(m.chat.id, "🔍 Please enter your postcode:")

@bot.message_handler(func=lambda m: sessions.get(m.chat.id, {}).get("step") == "awaiting_postcode")
def handle_postcode_input(m):
    user = m.chat.id
    pc = m.text.strip().replace(" ", "").upper()

    if pc in tracking_data and tracking_data[pc]:
        tracking = tracking_data[pc][0]['tracking']
        bot.send_message(user, "📦 *Your tracking reference:*", parse_mode="Markdown")
        time.sleep(2.5)
        bot.send_message(user, f"`{tracking}`", parse_mode="Markdown")
        time.sleep(2.5)
        bot.send_message(user, f"🔗 Track your item: {ROYAL_MAIL_TRACKING_URL}")
    else:
        bot.send_message(user, "❌ No tracking found for that postcode.")

    sessions[user].pop("step", None)

# === BROADCAST MODE ===
@bot.callback_query_handler(func=lambda call: call.data == 'broadcast')
def handle_broadcast_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    sessions[call.from_user.id] = {"step": "broadcast_waiting"}
    bot.send_message(call.from_user.id, "📣 Send your message now to broadcast it to all users.")
    threading.Timer(30, lambda: sessions.pop(call.from_user.id, None)).start()

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(m):
    if m.chat.id != ADMIN_ID:
        return
    sessions[m.chat.id] = {"step": "broadcast_waiting"}
    bot.send_message(m.chat.id, "📣 Send your message now to broadcast it to all users.")
    threading.Timer(30, lambda: sessions.pop(m.chat.id, None)).start()

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and "broadcast" in m.text.lower())
def broadcast_mode(m):
    sessions[m.chat.id] = {"step": "broadcast_waiting"}
    bot.send_message(m.chat.id, "📣 Send your message now to broadcast it to all users.")
    threading.Timer(30, lambda: sessions.pop(m.chat.id, None)).start()

@bot.message_handler(func=lambda m: sessions.get(m.chat.id, {}).get("step") == "broadcast_waiting")
def send_broadcast(m):
    text = m.text
    for uid in user_db.keys():
        try:
            bot.send_message(int(uid), text)
        except Exception as e:
            print(f"Failed to send to {uid}: {e}")
    bot.send_message(m.chat.id, "✅ Broadcast sent to all users!")
    sessions.pop(m.chat.id, None)

# === START BOT ===
bot.polling(none_stop=True)
