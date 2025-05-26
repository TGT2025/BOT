# ==== START BATCH 1: imports, global defs, setup ====

print("🧠 PAYMENT HANDLER LOADED")

import time
import re
import threading
import os
import logging
import json

from bot_instance import bot
from config import ADMIN_ID
from state import sessions, user_order_map
from utils.woo_api import get_order_details, issue_refund_coupon
from utils.file_ops import get_next_payment_method, set_last_payment_method

from utils.helpers import (
    get_revolut_reference,
    get_revolut_account,
    get_revolut_artisan,
    get_wise_account,
    get_wise_reference,
    get_wise_invoice_meta
)

from utils.invoice_generator import generate_reference, generate_invoice
from utils.user_store import has_used_paysafe, mark_paysafe_used, add_transaction
from web.paysafe_locator import find_paysafecard_locations
from utils.service_logic import select_service, update_client_history, clean_name, clean_address

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ✅ Store invoice sequence safely inside /data/
GLOBAL_SEQ_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "global_invoice_sequence.json")
print("📦 Using GLOBAL_SEQ_FILE:", GLOBAL_SEQ_FILE)

def get_global_sequence():
    if os.path.exists(GLOBAL_SEQ_FILE):
        with open(GLOBAL_SEQ_FILE, 'r') as f:
            data = json.load(f)
            current = data.get("last", 0) + 1
    else:
        current = 1

    with open(GLOBAL_SEQ_FILE, 'w') as f:
        json.dump({"last": current}, f)

    return current

def fetch_stores_async(user_id, postcode):
    store_text = find_paysafecard_locations(postcode)
    if user_id in sessions:
        sessions[user_id]['stores'] = store_text

def debug_log_all(m):
    from state import sessions
    print(f"🪵 DEBUG TEXT: {repr(m.text)} | TYPE: {m.content_type} | STEP: {sessions.get(m.chat.id, {}).get('step')}")

# ==== START BATCH 2: Pay flow (order input and processing) ====

# ✅ Track user's "💳 Pay" message
@bot.message_handler(func=lambda m: m.text == "💳 Pay")
def start_payment(m):
    user = m.chat.id
    print(f"🧠 .Pay triggered by {user}")
    current_step = sessions.get(user, {}).get("step", "")

    if current_step in ["awaiting_code", "awaiting_bank_screenshot", "awaiting_receipt_photo"]:
        msg = bot.send_message(user,
            "⚠️ You're already in the middle of a payment.\n\nPlease upload your screenshot or receipt. Type /start to restart.",
            parse_mode="Markdown")
        sessions[user].setdefault("message_log", []).append(msg.message_id)
        return

    if user not in sessions:
        sessions[user] = {}
    else:
        preserved = sessions[user].copy()
        logging.debug(f"[SESSION BEFORE PAY] {preserved}")

    sessions[user]["step"] = "awaiting_order"
    sessions[user]["message_log"] = []
    logging.debug(f"[SESSION AFTER PAY] {sessions[user]}")

    sessions[user]["message_log"].append(m.message_id)

    print(f"📦 Awaiting order number from user {user}")
    msg = bot.send_message(user, "👋 Please send your order number:")
    sessions[user]["message_log"].append(msg.message_id)


# ✅ Track user's order number input
@bot.message_handler(func=lambda m: sessions.get(m.chat.id, {}).get("step") == "awaiting_order" and m.text.isdigit())
def handle_order_number(m):
    user = m.chat.id
    sessions[user].setdefault("message_log", []).append(m.message_id)
    order_id = m.text.strip()
    order = get_order_details(order_id)

    if not order:
        msg = bot.send_message(user, "❌ Invalid order number.")
        sessions[user]["message_log"].append(msg.message_id)
        return

    user_order_map[order_id] = user
    total = float(order['total'])
    postcode = order['shipping']['postcode']
    items = "\n".join([f"- {i['name']} x{i['quantity']} — £{i['total']}" for i in order['line_items']])
    shipping_method = order['shipping_lines'][0]['method_title']
    shipping_cost = order.get('shipping_total', '0.00')

    raw_method = order.get('payment_method_title', '').lower().strip()
    print(f"[DEBUG] Woo method: {raw_method} → {raw_method}")

    if "paysafe" in raw_method:
        payment_method = "paysafecard"
    elif "bank" in raw_method or "card" in raw_method:
        payment_method = "bank"
    else:
        payment_method = "unknown"

    msg = bot.send_message(
        user,
        f"✅ *Order Confirmed!*\n\n📦 *Items Ordered:*\n{items}\n\n🚚 *Shipping:* {shipping_method} - £{shipping_cost}",
        parse_mode="Markdown"
    )
    sessions[user]["message_log"].append(msg.message_id)
    time.sleep(3)

    # ==== Paysafecard logic ====

    if payment_method in ["paysafe", "paysafecard"]:
        if has_used_paysafe(user):
            msg = bot.send_message(user, "💡 Welcome back! Since you've paid with Paysafecard before, we'll skip the intro.", parse_mode="Markdown")
            sessions[user]["message_log"].append(msg.message_id)
            time.sleep(2)
            sessions[user].update({"step": "awaiting_code", "order_id": order_id})
            msg = bot.send_message(user, f"💷 *Order Total:* £{total:.2f}", parse_mode="Markdown")
            sessions[user]["message_log"].append(msg.message_id)
            msg = bot.send_message(user, "📸 Please send an image of your Paysafecard receipt showing all corners.", parse_mode="Markdown")
            sessions[user]["message_log"].append(msg.message_id)
            mark_paysafe_used(user)
            add_transaction(user, {
                "order_id": order_id,
                "amount": total,
                "currency": "GBP",
                "payment_method": "Paysafecard",
                "account_paid_to": "N/A"
            })
            return

        sessions[user].update({"step": "awaiting_code", "order_id": order_id, "stores": None})
        threading.Thread(target=fetch_stores_async, args=(user, postcode)).start()

        msg = bot.send_message(user, "🔗 *How to Pay with Paysafecard*", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2.5)

        msg = bot.send_message(user, "💳 Paysafecard is a quick, secure, and anonymous payment method available at thousands of PayPoint locations nationwide.", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2.5)

        with open(os.path.join(os.path.dirname(__file__), "..", "assets", "paypoint1.png"), "rb") as img1:
            msg = bot.send_photo(user, img1)
            sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2.5)

        msg = bot.send_message(user, "To keep transactions anonymous, we only accept Paysafecards bought in physical stores. Online codes will not be accepted.", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2.5)

        with open(os.path.join(os.path.dirname(__file__), "..", "assets", "paypoint2.png"), "rb") as img2:
            msg = bot.send_photo(user, img2)
            sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2.5)

        msg = bot.send_message(user, "You can pay with card or cash instantly and will be issued a paper receipt that contains a 16-digit PIN. This PIN is all we need to process your order.", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2.5)

        with open(os.path.join(os.path.dirname(__file__), "..", "assets", "paypoint3.png"), "rb") as img3:
            msg = bot.send_photo(user, img3)
            sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2.5)

        msg = bot.send_message(user, "💡 Paysafecards are sold in voucher set values of £10, £25, £50, £75, and £100 — which can be combined if necessary.", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2.5)

        msg = bot.send_message(user, "💰 Any overpayments will automatically be refunded as a coupon, which can be used in-store.", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2)

        msg = bot.send_message(user, "🔍 Searching for locations near you...", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2)

        for _ in range(12):
            store_text = sessions.get(user, {}).get("stores")
            if store_text:
                break
            time.sleep(1)

        store_text = sessions.get(user, {}).get("stores")
        if store_text:
            msg = bot.send_message(user, store_text, parse_mode="Markdown")
            sessions[user]["message_log"].append(msg.message_id)
            time.sleep(2.5)

        msg = bot.send_message(user, f"💷 *Order Total:* £{total:.2f}", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2)

        msg = bot.send_message(user, "⏳ There is no time limit to complete your order.", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2)

        msg = bot.send_message(user, "Buy PaysafeCard - Send us the PIN - We Process your Order - Postie Delivers", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2.5)

        with open(os.path.join(os.path.dirname(__file__), "..", "assets", "paypoint4.png"), "rb") as img4:
            msg = bot.send_photo(user, img4)
            sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2)

        msg = bot.send_message(user, "🔑 Once you have the PIN, please send an image of your receipt clearly showing all four corners.", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)

        mark_paysafe_used(user)
        add_transaction(user, {
            "order_id": order_id,
            "amount": total,
            "currency": "GBP",
            "payment_method": "Paysafecard",
            "account_paid_to": "N/A"
        })
        return

    # ==== ROTATED PAYMENT METHOD LOGIC ====

    # ==== ROTATED PAYMENT METHOD LOGIC ====
    client_name = clean_name(f"{order['billing']['first_name']} {order['billing']['last_name']}")
    sequence = get_global_sequence()
    method = get_next_payment_method(total)

    reference = None
    account = None
    service = ""
    description = ""

    if method == "revolut2":
        try:
            account = get_revolut_artisan(total, "private") or get_revolut_artisan(total, "market")
            service = "Revolut – Artisan"
            description = "Processed via Artisan Tile Rotation."
        except ValueError as artisan_error:
            print(f"[Fallback] Artisan payment failed: {artisan_error}. Trying Wise...")
            try:
                account = get_wise_account()
                meta = get_wise_invoice_meta(total)
                reference = generate_reference(meta["code"], client_name, sequence)
                service = meta["name"]
                description = meta["description"]
                account["reference"] = reference
                method = "wise"
                print(f"[WISE] Wise selected with service {service}")
            except WiseNotAvailable as wise_error:
                print(f"[Fallback] Wise also not available: {wise_error}. Using Pantelis Revolut backup...")
                account = get_revolut_account(total)
                service = "Revolut – Pantelis"
                description = "Processed via Pantelis Fallback"
                method = "revolut"

        if account and "reference" in account and not reference:
            reference = account["reference"]

    elif method == "wise":
        try:
            account = get_wise_account()
            meta = get_wise_invoice_meta(total)
            reference = generate_reference(meta["code"], client_name, sequence)
            service = meta["name"]
            description = meta["description"]
            account["reference"] = reference
        except Exception as e:
            print(f"[WISE FALLBACK] Wise unavailable, switching to Revolut: {e}")
            account = get_revolut_account(total)
            if account and "reference" in account:
                reference = account["reference"]
                service = "Revolut – Pantelis"
                description = "Wise fallback – processed via Pantelis"
                method = "revolut"

    else:
        account = get_revolut_account(total)
        if account and "reference" in account:
            reference = account["reference"]
            service = "Revolut – Pantelis"
            description = "Processed via Pantelis (Main Account)."

    if not reference:
        print(f"[⚠️ REFERENCE MISSING] Fallback triggered for order {order_id}")
        reference = f"FALLBACK-{order_id}"
        account = {"reference": reference}
        service = "Fallback Payment"
        description = "No reference generated – fallback used"

    set_last_payment_method(method)

    sessions[user].update({
        "reference": reference,
        "service": service,
        "description": description,
        "order_id": order_id,
        "has_sent_proof": False,
        "has_typed_paid": False,
        "step": "awaiting_bank_screenshot",
        "last_method": method,
        "payment_account": account
    })
    # ==== SENDING PAYMENT INSTRUCTIONS ====

    # 1️⃣ Payment Info Header
    msg = bot.send_message(user, "🔐 *Payment Info*", parse_mode="Markdown")
    sessions[user]["message_log"].append(msg.message_id)
    time.sleep(2)

    # 2️⃣ Security Message
    msg = bot.send_message(user,
        "For security reasons we rotate our payment methods and references for every order. "
        "You may receive details for a BACS transfer or a secure payment link.",
        parse_mode="Markdown")
    sessions[user]["message_log"].append(msg.message_id)
    time.sleep(2.5)

    # 3️⃣ Payment Method Title
    if method == "wise":
        msg = bot.send_message(user, "🏦 *Payment via BACS transfer*", parse_mode="Markdown")
    else:
        msg = bot.send_message(user, "🏦 *Payment via Revolut*", parse_mode="Markdown")
    sessions[user]["message_log"].append(msg.message_id)
    time.sleep(2)

    # 4️⃣ Payment Reference Label
    msg = bot.send_message(user, "🧾 *Payment Reference:*", parse_mode="Markdown")
    sessions[user]["message_log"].append(msg.message_id)
    time.sleep(1.5)

    # 5️⃣ Payment Reference Code
    msg = bot.send_message(user, f"`{reference}`", parse_mode="Markdown")
    sessions[user]["message_log"].append(msg.message_id)
    time.sleep(1.5)

    # 6️⃣ Warning about Reference
    msg = bot.send_message(user,
        "⚠️ Please ensure to include the reference we have provided above. "
        "Anything else like your order number can flag our account.",
        parse_mode="Markdown")
    sessions[user]["message_log"].append(msg.message_id)
    time.sleep(2)

    # 7️⃣ Bank Details if Wise
    if method == "wise":
        if all(k in account for k in ("holder", "bank_sort", "bank_acc")):
            msg = bot.send_message(user,
                f"• Name: {account['holder']}\n"
                f"• Sort Code: {account['bank_sort']}\n"
                f"• Account Number: {account['bank_acc']}\n"
                f"• Bank: Wise Business",
                parse_mode="Markdown")
            sessions[user]["message_log"].append(msg.message_id)
            time.sleep(2)

    # 8️⃣ Secure Link (if available)
    if 'link' in account and account['link'].startswith("http"):
        msg = bot.send_message(user, f"🔗 {account['link']}", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        time.sleep(2)

    # 9️⃣ Order Total
    msg = bot.send_message(user, f"💷 *Order Total:* £{total:.2f}", parse_mode="Markdown")
    sessions[user]["message_log"].append(msg.message_id)
    time.sleep(2)

    # 🔟 Prompt for Proof
    msg = bot.send_message(user, "📸 Once paid, please upload a screenshot here.", parse_mode="Markdown")
    sessions[user]["message_log"].append(msg.message_id)

# ==== START BATCH 3: ADMIN CONFIRMATION & INVOICE ====

@bot.message_handler(func=lambda m: m.reply_to_message and m.from_user.id == ADMIN_ID)
def handle_admin_reply(m):
    import traceback
    from utils.invoice_generator import create_invoice_pdf, pdf_safe
    from utils.woo_api import get_order_details, issue_refund_coupon
    from utils.service_logic import clean_name, clean_address

    text = m.text.strip().upper()
    original_text = m.reply_to_message.text or ""
    match = re.search(r'Order: (\d+)', original_text)
    if not match:
        logging.warning("[DEBUG] No order ID found in admin reply")
        return

    order_id = match.group(1)
    customer_id = None
    for uid, sess in sessions.items():
        if sess.get("order_id") == order_id:
            customer_id = uid
            break

    if not customer_id:
        logging.error(f"[INVOICE] Unable to match order {order_id} to any session")
        bot.send_message(m.chat.id, f"❌ Unable to locate session for order {order_id}.")
        return

    order = get_order_details(order_id)
    if not isinstance(order, dict) or 'billing' not in order:
        logging.error(f"[INVOICE] Invalid Woo order object for ID {order_id}: {order}")
        bot.send_message(m.chat.id, f"❌ Could not retrieve valid order data for {order_id}. Invoice not created.")
        return

    total = float(order['total'])
    email = order['billing']['email']
    session_data = sessions.get(customer_id, {})
    method = order.get('payment_method_title', '').strip().lower()

    if method not in ["revolut", "paysafe", "paysafecard", "wise"]:
        method = session_data.get("last_method", method)

    if method in ["paysafe", "paysafecard"]:
        reference = "PSF-N/A"
        account = {"holder": "Paysafe Payment", "reference": "PSF-N/A"}
        service_name = "Paysafecard"
        description = "Anonymous payment via retail voucher"
    else:
        reference = session_data.get("reference")
        account = session_data.get("payment_account", {})
        service_name = session_data.get("service", "Custom Service")
        description = session_data.get("description", "Manual invoice after admin confirmation")

    if not reference and method not in ["paysafe", "paysafecard"]:
        logging.error(f"[INVOICE] BLOCKED: No reference in session for order {order_id}")
        bot.send_message(m.chat.id, f"❌ Reference not found for order {order_id}. Invoice not created.")
        return

    client_name = clean_name(f"{order['billing']['first_name']} {order['billing']['last_name']}")
    client_phone = order['billing']['phone']
    client_address = clean_address("\n".join(filter(None, [
        order['billing']['address_1'],
        order['billing']['address_2'],
        order['billing']['city'],
        order['billing']['postcode'],
        order['billing']['country']
    ])))
    client_data = {
        "name": client_name,
        "email": email,
        "address": client_address
    }

    safe_reference = pdf_safe(reference)
    invoice_path = os.path.join("invoices", f"{safe_reference}.pdf")

    def send_confirmation_to_user(amount, customer_id):
        logging.info(f"📨 send_confirmation_to_user() running for {customer_id}")
        msg_ids = sessions[customer_id].setdefault("message_log", [])

        msg1 = bot.send_message(customer_id, f"💰 Your payment of £{amount:.2f} has been received.", parse_mode="Markdown")
        msg_ids.append(msg1.message_id)
        time.sleep(2)

        if method in ["paysafe", "paysafecard"]:
            refund = round(amount - total, 2)
            if refund > 0:
                msg_coupon = bot.send_message(customer_id, f"💰 Overpayment: £{refund:.2f}", parse_mode="Markdown")
                msg_ids.append(msg_coupon.message_id)
                coupon = issue_refund_coupon(total, amount, email)
                if coupon:
                    msg_coupon_label = bot.send_message(customer_id, "🎟️ Refund Coupon:", parse_mode="Markdown")
                    msg_coupon_code = bot.send_message(customer_id, f"`{coupon}`", parse_mode="Markdown")
                    msg_ids.extend([msg_coupon_label.message_id, msg_coupon_code.message_id])
            time.sleep(2)

        msg2 = bot.send_message(customer_id, "🛒 Your order is now being prepared for dispatch.", parse_mode="Markdown")
        msg_ids.append(msg2.message_id)
        time.sleep(2)

        msg3 = bot.send_message(customer_id, "📦 If you are receiving this message before 10am Monday to Friday your order will be shipped same day.", parse_mode="Markdown")
        msg_ids.append(msg3.message_id)
        time.sleep(2)

        msg4 = bot.send_message(customer_id, "📬 You can retrieve tracking shortly after dispatch.", parse_mode="Markdown")
        msg_ids.append(msg4.message_id)
        time.sleep(2)

        msg5 = bot.send_message(customer_id, "🍀 Lots of love,\nTGT", parse_mode="Markdown")
        msg_ids.append(msg5.message_id)
        time.sleep(0.5)

        wipe_msg_text = (
            "🛡️ To keep your data safe, this chat will be deleted in 8 hours. Please save your refund coupon (if one was issued)."
            if method in ["paysafe", "paysafecard"]
            else "🛡️ To keep your data safe, this chat will be deleted in 8 hours."
        )
        wipe_msg = bot.send_message(customer_id, wipe_msg_text, parse_mode="Markdown")
        msg_ids.append(wipe_msg.message_id)

        def wipe_user_messages():
            time.sleep(28800)
            for msg_id in msg_ids:
                try:
                    bot.delete_message(customer_id, msg_id)
                except Exception as e:
                    logging.warning(f"[WIPE ERROR] Could not delete message {msg_id}: {e}")
            sessions.pop(customer_id, None)

        threading.Thread(target=wipe_user_messages).start()

    def generate_invoice(amount):
        try:
            create_invoice_pdf(
                ref=reference,
                client=client_data,
                service_name=service_name,
                service_description=description,
                amount=amount,
                client_phone=client_phone,
                output_path=invoice_path
            )
            logging.info(f"[INVOICE] Created: {invoice_path}")
            bot.send_message(m.chat.id, f"✅ Invoice generated and saved: {reference}")
        except Exception as e:
            logging.error(f"[INVOICE] Creation failed: {e}")
            bot.send_message(m.chat.id, "❌ Failed to generate invoice.")

    if text.startswith("OK"):
        try:
            paid = float(text[2:].strip()) if len(text) > 2 else total
            send_confirmation_to_user(paid, customer_id)
            if method == "wise":
                generate_invoice(paid)
        except Exception as e:
            logging.error(f"[INVOICE] Exception: {e}")
            logging.error(traceback.format_exc())
            bot.send_message(customer_id, "❌ Unable to process payment. Please contact support.")

# ==== START BATCH 4: HANDLE PROOF & SCREENSHOTS ====

@bot.message_handler(
    func=lambda m: sessions.get(m.chat.id, {}).get("step") in [
        "awaiting_code", "awaiting_bank_screenshot", "awaiting_receipt_photo"
    ],
    content_types=['text', 'photo', 'sticker', 'voice', 'contact', 'location', 'document']
)
def handle_code_or_screenshot(m):
    import os
    import time
    import threading
    from state import sessions
    from utils.woo_api import get_order_details
    from utils.invoice_generator import generate_invoice

    print("✅ handle_code_or_screenshot triggered")
    user = m.chat.id
    session = sessions.get(user, {})
    step = session.get("step")
    order_id = session.get("order_id")

    if step not in ["awaiting_code", "awaiting_bank_screenshot", "awaiting_receipt_photo"]:
        return

    order = get_order_details(order_id)
    if not order:
        msg = bot.send_message(user, "❌ Couldn't load your order. Please restart with /start.", parse_mode="Markdown")
        sessions[user].setdefault("message_log", []).append(msg.message_id)
        return

    total = float(order['total'])
    method = session.get("last_method", "").lower()
    account = session.get("payment_account", {})
    is_paysafe = method in ["paysafe", "paysafecard"]

    # === PAYSAFE LOGIC ===
    if is_paysafe:
        if m.content_type not in ["photo", "document"]:
            msg = bot.send_message(user, "⚠️ Please upload an image of your Paysafecard receipt to continue.", parse_mode="Markdown")
            sessions[user].setdefault("message_log", []).append(msg.message_id)
            return

        sessions[user].setdefault("message_log", []).append(m.message_id)

        file_id = m.photo[-1].file_id if m.content_type == "photo" else m.document.file_id
        uploads = session.get("uploads", [])
        uploads.append(file_id)
        sessions[user]["uploads"] = uploads
        sessions[user]["step"] = "awaiting_code"

        if not session.get("upload_timer_started"):
            sessions[user]["upload_timer_started"] = True
            msg = bot.send_message(user, "✅ Receipt received. You may upload more images within 20 seconds if needed.", parse_mode="Markdown")
            sessions[user]["message_log"].append(msg.message_id)

            def forward_paysafe_batch():
                time.sleep(20)
                print(f"⏳ Waiting complete. Forwarding Paysafe uploads for user {user}")
                upload_files = sessions[user].get("uploads", [])
                if not upload_files:
                    msg = bot.send_message(user, "⚠️ No valid uploads found. Please try again.", parse_mode="Markdown")
                    sessions[user]["message_log"].append(msg.message_id)
                    return

                summary = f"🛒 Order: {order_id}\n💳 Payment Method: Paysafecard"
                msg = bot.send_message(ADMIN_ID, summary, parse_mode="Markdown")
                sessions[user]["admin_msg_id"] = msg.message_id

                for fid in upload_files:
                    bot.send_document(ADMIN_ID, fid)

                msg = bot.send_message(user, "🙏🏼 Thanks! Your receipt(s) have been submitted. Await admin confirmation.", parse_mode="Markdown")
                sessions[user]["message_log"].append(msg.message_id)
                print("✅ Paysafe receipt batch submitted.")

            threading.Thread(target=forward_paysafe_batch).start()

        return

    # === WISE / REVOLUT LOGIC ===
    if m.content_type in ["photo", "document"]:
        sessions[user].setdefault("message_log", []).append(m.message_id)

        file_id = m.photo[-1].file_id if m.content_type == "photo" else m.document.file_id
        sessions[user]["has_sent_proof"] = True
        sessions[user]["proof_uploaded_at"] = time.time()
        sessions[user]["pending_photo_file_id"] = file_id
        sessions[user]["step"] = "awaiting_confirmation"

        reference = session.get("reference", "")
        summary = (
            f"🛒 Order: {order_id}\n"
            f"💳 Paid £{total:.2f}\n"
            f"💳 Payment Method: {method.capitalize()}"
        )

        if reference:
            summary += f"\n🧾 Reference: {reference}"

        if method not in ["paysafe", "paysafecard"]:
            account_info = account.get("holder") or account.get("link") or "N/A"
            summary += f"\n📥 Account: {account_info}"

        msg = bot.send_message(ADMIN_ID, summary, parse_mode="Markdown")
        sessions[user]["admin_msg_id"] = msg.message_id

        bot.forward_message(ADMIN_ID, user, m.message_id)

        if method == "wise":
            invoice_path = generate_invoice(
                order_id,
                session.get("reference", ""),
                session.get("service", ""),
                session.get("description", "")
            )
            if invoice_path and os.path.exists(invoice_path):
                from logging import info
                info(f"[INVOICE] Saved to file system: {invoice_path}")

        msg = bot.send_message(user, "🙏🏼 Thanks! Your payment has been sent for review. You’ll receive a confirmation shortly.", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)
        print("✅ Flow complete. Awaiting admin confirmation.")

    else:
        msg = bot.send_message(user, "⚠️ Please upload a valid screenshot or receipt (photo/document).", parse_mode="Markdown")
        sessions[user]["message_log"].append(msg.message_id)

# ==== END OF BATCH 4 ====
