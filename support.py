from bot_instance import bot
from state import sessions

@bot.message_handler(func=lambda m: m.text == "💬 Support")
def handle_support(m):
    step = sessions.get(m.chat.id, {}).get("step")
    if step in ["awaiting_code", "awaiting_bank_screenshot", "awaiting_receipt_photo"]:
        bot.send_message(
            m.chat.id,
            "⚠️ You're currently in a payment process.\nPlease upload your proof and type *paid*.\nUse /start to cancel.",
            parse_mode="Markdown"
        )
        return

    bot.send_message(
        m.chat.id,
        "📞 Contact support via Telegram:\n@tistgt"
    )
