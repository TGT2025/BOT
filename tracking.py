from bot_instance import bot
from config import ROYAL_MAIL_TRACKING_URL
from utils.file_ops import tracking_data
from state import sessions
import time

@bot.message_handler(func=lambda m: m.text == "📦 Track")
def handle_tracking_request(m):
    # Always (re)create session if missing
    if m.chat.id not in sessions:
        sessions[m.chat.id] = {}
    step = sessions[m.chat.id].get("step")
    if step in ["awaiting_code", "awaiting_bank_screenshot", "awaiting_receipt_photo"]:
        bot.send_message(m.chat.id, "⚠️ You're in a payment process. Please upload your proof and type *paid*.\nUse /start to cancel.", parse_mode="Markdown")
        return

    sessions[m.chat.id]["step"] = "awaiting_postcode"
    bot.send_message(m.chat.id, "🔍 Please enter your postcode:")

@bot.message_handler(func=lambda m: sessions.get(m.chat.id, {}).get("step") == "awaiting_postcode")
def handle_postcode_input(m):
    # Always (re)create session if missing
    if m.chat.id not in sessions:
        sessions[m.chat.id] = {}
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

    # Only clear step, not full session
    if user in sessions:
        sessions[user].pop("step", None)