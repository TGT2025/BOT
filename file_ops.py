import json
import os
from datetime import datetime, timedelta
from config import TRACKING_FILE, USER_DB_FILE
from utils.helpers import get_revolut_artisan

# === Runtime storage ===
tracking_data = {}
user_db = set()
rotation_state = {"last_method": "revolut"}  # Default first payment method

ROTATION_FILE = 'rotation.json'

# === Load users ===
if os.path.exists(USER_DB_FILE):
    with open(USER_DB_FILE, 'r') as f:
        try:
            user_db = set(json.load(f))
        except:
            user_db = set()

# === Load tracking ===
if os.path.exists(TRACKING_FILE):
    with open(TRACKING_FILE, 'r') as f:
        try:
            tracking_data = json.load(f)
        except:
            tracking_data = {}

# === Load rotation state ===
if os.path.exists(ROTATION_FILE):
    with open(ROTATION_FILE, 'r') as f:
        try:
            rotation_state = json.load(f)
            if not isinstance(rotation_state, dict) or "last_method" not in rotation_state:
                print("[WARN] Invalid rotation format, resetting.")
                rotation_state = {"last_method": "revolut"}
        except Exception as e:
            print(f"[WARN] Failed to load rotation.json: {e}")
            rotation_state = {"last_method": "revolut"}

# === Rotation logic (revolut2 = Youssef, revolut = Pantelis, wise = BACS) ===
def get_next_payment_method(order_total: float):
    global rotation_state
    rotation_order = ["revolut2", "revolut", "wise"]
    last = rotation_state.get("last_method", "revolut")

    if last not in rotation_order:
        last = "revolut"

    start_index = (rotation_order.index(last) + 1) % len(rotation_order)

    for i in range(len(rotation_order)):
        candidate = rotation_order[(start_index + i) % len(rotation_order)]

        if candidate == "revolut2":
            try:
                artisan_private = get_revolut_artisan(order_total, "private")
                artisan_market = get_revolut_artisan(order_total, "market")
                if artisan_private or artisan_market:
                    rotation_state["last_method"] = "revolut2"
                    save_rotation()
                    return "revolut2"
            except ValueError as e:
                print(f"[ARTISAN FAILSAFE] Artisan payment unavailable: {e}")
                # fall through to next method

        elif candidate == "revolut":
            rotation_state["last_method"] = "revolut"
            save_rotation()
            return "revolut"

        elif candidate == "wise":
            if order_total >= 150:
                rotation_state["last_method"] = "wise"
                save_rotation()
                return "wise"

    # Final fallback
    rotation_state["last_method"] = "revolut"
    save_rotation()
    return "revolut"

def set_last_payment_method(method):
    rotation_state["last_method"] = method
    save_rotation()

def save_rotation():
    with open(ROTATION_FILE, "w") as f:
        json.dump(rotation_state, f, indent=2)

def save_users():
    with open(USER_DB_FILE, 'w') as f:
        json.dump(list(user_db), f)

def save_tracking():
    cutoff = datetime.now() - timedelta(days=10)
    for pc in list(tracking_data):
        entries = [e for e in tracking_data[pc] if datetime.fromisoformat(e['date']) > cutoff]
        if entries:
            tracking_data[pc] = entries
        else:
            del tracking_data[pc]
    with open(TRACKING_FILE, 'w') as f:
        json.dump(tracking_data, f, indent=2)
