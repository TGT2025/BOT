# handlers/broadcast.py

from bot_instance import bot
from config import ADMIN_ID
from state import sessions
import threading
import time

# ✅ Load real user data from file
import json
import os
with open("user_data.json", "r") as f:
    user_db = json.load(f)

# ✅ Handle inline button with callback_data='broadcast'
@bot.callback_query_handler(func=lambda call: call.data == 'broadcast')
def handle_broadcast_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    print(f"[BROADCAST MODE] Triggered via inline button by {call.from_user.id}")
    bot.answer_callback_query(call.id)
    sessions[call.from_user.id] = {"step": "broadcast_waiting"}
    bot.send_message(call.from_user.id, "📣 Send your message now to broadcast it to all users.")

# ✅ Optional: /broadcast command fallback
@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(m):
    if m.chat.id != ADMIN_ID:
        return
    print(f"[BROADCAST MODE] Triggered via /broadcast by {m.chat.id}")
    sessions[m.chat.id] = {"step": "broadcast_waiting"}
    bot.send_message(m.chat.id, "📣 Send your message now to broadcast it to all users.")

# ✅ Handle typed "📣 Broadcast" text
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and "broadcast" in m.text.lower())
def broadcast_mode(m):
    print(f"[BROADCAST MODE] Triggered via text by {m.chat.id}")
    sessions[m.chat.id] = {"step": "broadcast_waiting"}
    bot.send_message(m.chat.id, "📣 Send your message now to broadcast it to all users.")

# ✅ Broadcast handler with timed deletion
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'animation'])
def broadcast_handler(m):
    if sessions.get(m.chat.id, {}).get("step") != "broadcast_waiting" or m.chat.id != ADMIN_ID:
        return

    sent = 0
    failed = 0

    print(f"[DEBUG] user_db type: {type(user_db)}")
    print(f"[DEBUG] user_db preview: {repr(user_db)[:500]}")
    print(f"[DEBUG] incoming content_type: {m.content_type}")

    all_user_ids = [int(uid) for uid in user_db]

    print(f"[BROADCAST] Sending to {len(all_user_ids)} users...")

    for uid in all_user_ids:
        try:
            if m.content_type == "text":
                msg = bot.send_message(uid, m.text)
            elif m.content_type == "photo":
                msg = bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption or "")
            elif m.content_type == "video":
                msg = bot.send_video(uid, m.video.file_id, caption=m.caption or "")
            elif m.content_type == "document":
                msg = bot.send_document(uid, m.document.file_id, caption=m.caption or "")
            elif m.content_type == "animation":
                msg = bot.send_animation(uid, m.animation.file_id, caption=m.caption or "")

            print(f"[✅ SENT] → {uid}")
            sent += 1

            # 🔐 Auto-delete broadcasts after 8 hours (28800s)
            def wipe_broadcast(uid, msg_id):
                time.sleep(28800)  # ⏱️ 8 hours in seconds
                try:
                    bot.delete_message(uid, msg_id)
                    print(f"🧼 Wiped broadcast for {uid}")
                except Exception as e:
                    print(f"[WIPE ERROR] Failed to delete broadcast {uid}: {e}")

            threading.Thread(target=wipe_broadcast, args=(uid, msg.message_id)).start()

        except Exception as e:
            print(f"[❌ FAIL] → {uid}: {e}")
            failed += 1
            continue

    bot.send_message(m.chat.id, f"✅ Broadcast sent to {sent}/{len(all_user_ids)} users.")
    if failed:
        bot.send_message(m.chat.id, f"⚠️ Failed to deliver to {failed} users.")
    sessions[m.chat.id] = {}
    print("[BROADCAST DONE]")

# 🔍 DEBUG: log all text messages from admin (placed last to not override others)
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and "debug" in m.text.lower(), content_types=['text'])
def debug_log_text(m):
    print(f"[DEBUG TEXT] From {m.chat.id}: {repr(m.text)}")

# 🔍 DEBUG: log all inline callback data
@bot.callback_query_handler(func=lambda call: True)
def debug_log_callback(call):
    print(f"[DEBUG CALLBACK] From {call.from_user.id}: {call.data}")
