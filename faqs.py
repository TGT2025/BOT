from bot_instance import bot
from state import sessions

@bot.message_handler(commands=['faqs'])
@bot.message_handler(func=lambda m: m.text and "faq" in m.text.lower())
def faqs(m):
    # 🔐 Block if user is mid-payment
    step = sessions.get(m.chat.id, {}).get("step")
    if step in ["awaiting_code", "awaiting_bank_screenshot", "awaiting_receipt_photo"]:
        bot.send_message(m.chat.id, "⚠️ You're currently in a payment process. Please upload your proof and type *paid*.\nUse /start to cancel.", parse_mode="Markdown")
        return

    faqs_text = "📘 *Frequently Asked Questions:*\n\n"

    faqs = {
        "What is Paysafecard?": "A prepaid 16-digit code used for secure, private online payments — no bank or personal info needed.",
        "Where can I buy Paysafecard?": "You can purchase one in-store at PayPoint locations using cash or debit card.",
        "Do I need to register an account?": "❌ No registration is required. Just buy a card and send us the 16-digit PIN directly.",
        "How do I pay with a voucher?": "Simply send the 16-digit PIN to the bot. That’s it — we’ll handle the rest.",
        "What amounts are available?": "Vouchers are commonly available in £10, £25, £50, £75, and £100 denominations.",
        "Can I combine multiple vouchers?": "✅ Yes, you can combine codes to cover the total payment amount.",
        "What happens if I overpay?": "You will be automatically issued a refund coupon that can be used in-store on your next purchase.",
        "What if I lose my voucher?": "🚫 Treat it like cash — lost or redeemed codes cannot be recovered or refunded.",
        "Why can't I buy online?": "Paysafecards purchased from the Paysafecard website cannot be processed as this may flag our account.",
        "I can’t get to a store — what do I do?": "In this case, you can buy the Paysafecard from https://www.mobiletopup.co.uk/paysafecard. Please note the site will charge a fee for purchasing, whereas in-store there is no fee.",
        "Can I reuse old bank transfer info?": "❗ Only use the bank account or link provided by this bot. We rotate them for security reasons to avoid account flags.",
        "When are payments processed?": "Payments are confirmed daily until 10AM, Monday to Friday. Orders paid before this cutoff are shipped same-day whenever possible.",
        "What happens after I pay?": "Once confirmed, we pack and dispatch your order. Tracking is always available on the bot daily after cutoff.",
        "How long will my order take to arrive?": "T48: 2–5 days\nT24: 1–3 days\nSD1PM: Next Day\nPlease note: Royal Mail may experience delays and these timeframes can vary.",
        "Is delivery guaranteed?": "✅ Yes — as long as the shipping address is correct, we guarantee your delivery.",
        "How do I track my order?": "Use the 📦 Track button in the bot menu and enter your postcode.",
        "I've tracked my order but there is no update?": "Please allow 12–24 hours for tracking to update as it moves through the Royal Mail system.",
        "Is this service legit and safe?": "💯 Yes — we operate like any other online store, with secure payments and tracked delivery.",
        "Is Paysafecard secure?": "✅ Absolutely. When paid in-store, it's anonymous, safe, and doesn’t require personal data."
    }

    for question, answer in faqs.items():
        faqs_text += f"*Q: {question}*\n{answer}\n\n"

    bot.send_message(
        m.chat.id,
        faqs_text.strip(),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
