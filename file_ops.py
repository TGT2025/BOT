import os
import json
from utils.helpers import get_revolut_artisan

ROTATION_STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "payment_rotation_tracker.json")
rotation_state = {}

def load_rotation():
    global rotation_state
    if os.path.exists(ROTATION_STATE_FILE):
        with open(ROTATION_STATE_FILE, "r") as f:
            rotation_state = json.load(f)
    else:
        rotation_state = {}

def save_rotation():
    with open(ROTATION_STATE_FILE, "w") as f:
        json.dump(rotation_state, f, indent=2)

def get_next_payment_method(order_total):
    global rotation_state
    rotation_order = ["revolut2", "revolut"]
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

    # Final fallback
    rotation_state["last_method"] = "revolut"
    save_rotation()
    return "revolut"

def set_last_payment_method(method):
    global rotation_state
    rotation_state["last_method"] = method
    save_rotation()