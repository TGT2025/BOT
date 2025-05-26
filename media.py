# handlers/media.py

from bot_instance import bot
from state import sessions, user_order_map
from config import ADMIN_ID
from utils.woo_api import get_order_details

@bot.message_handler(
    func=lambda m: sessions.get(m.chat.id, {}).get("step") in ["awaiting_code", "awaiting_bank_screenshot"],
    content_types=['photo']
)
def handle_photos(m):
    user = m.chat.id
    state = sessions.get(user, {})

    if state.get("step") in ["awaiting_code", "awaiting_bank_screenshot"]:
        order_id = state['order_id']
        order = get_order_details(order_id)
        if not order:
            bot.send_message(user, "❌ Could not load your order.")
            return

        total = order['total']
        user_order_map[order_id] = m.from_user.id

        if state['step'] == "awaiting_code":
            bot.send_message(ADMIN_ID, f"🛎️ Order: {order_id}\n💳 Total: £{total}\n💳 Paid via Paysafecard")
        else:
            bot.send_message(ADMIN_ID, f"🏦 Bank Transfer Screenshot\n🛒 Order: {order_id}\nFrom: {user}")

        bot.send_photo(ADMIN_ID, m.photo[-1].file_id)

        bot.send_message(user, "✅ Thank you. We process payments and orders up until our 10am cut off Monday to Friday. Please wait for confirmation.")
        sessions[user] = {}