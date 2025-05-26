# handlers/uploads.py

import os
from bot_instance import bot
from config import ADMIN_ID
from utils.pdf_parser import extract_tracking_from_pdf
from utils.file_ops import tracking_data, save_tracking

@bot.message_handler(func=lambda m: m.text == "📄 Upload Tracking" and m.chat.id == ADMIN_ID)
def upload_tracking(m):
    bot.send_message(m.chat.id, "📄 Send the tracking PDF now.")

@bot.message_handler(content_types=['document'])
def handle_pdf(m):
    if m.from_user.id != ADMIN_ID:
        return
    if not m.document.file_name.lower().endswith('.pdf'):
        bot.send_message(m.chat.id, "❌ Please upload a valid PDF file.")
        return

    file = bot.get_file(m.document.file_id)
    path = f"{m.document.file_id}.pdf"
    with open(path, 'wb') as f:
        f.write(bot.download_file(file.file_path))

    new_data = extract_tracking_from_pdf(path)

    # ✅ Overwrite old tracking for each postcode
    for pc, entries in new_data.items():
        tracking_data[pc] = entries  # Always keep only the latest

    save_tracking()
    os.remove(path)

    bot.send_message(m.chat.id, f"✅ {sum(len(v) for v in new_data.values())} tracking numbers saved.")