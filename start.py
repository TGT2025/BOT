from telebot import types
from bot_instance import bot
from config import ADMIN_ID
from utils.user_store import ensure_user
from state import sessions  # ✅ Session import to control user flow

@bot.message_handler(commands=['start'])
def start(m):
    # ✅ Safely initialize session if it doesn't exist
    if m.chat.id not in sessions:
        sessions[m.chat.id] = {}

    # ✅ Reset step only (preserve other session data if any)
    sessions[m.chat.id]['step'] = "awaiting_order"

    # ✅ Create or load user in persistent store
    ensure_user(
        user_id=str(m.chat.id),
        username=m.from_user.username if m.from_user else None
    )

    # 🧾 Keyboard setup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💳 Pay", "📦 Track")
    markup.row("📘 FAQs", "💬 Support")
    if m.chat.id == ADMIN_ID:
        markup.row("📤 Upload Tracking", "📣 Broadcast")

    # 👋 Welcome message
    welcome = (
        "🤖 Welcome to TGT's service bot.\n\n"
        "This bot was developed to streamline and improve your experience.\n\n"
        "Through this bot you can:\n"
        "- 💳 Pay for your order\n"
        "- 📦 Track your order\n"
        "- 📘 Read FAQs\n"
        "- 💬 Contact support\n"
        "- 🔊 Receive updates\n\n"
        "- 👉 Tap the 4-dot icon [🔳] below to open the menu."
    )

    bot.send_message(m.chat.id, welcome, reply_markup=markup)