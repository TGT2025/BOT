import json
import os
from datetime import datetime
from threading import Lock

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'user_data.json')
_data_lock = Lock()


def _read_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with _data_lock:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}


def _write_data(data):
    with _data_lock:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


def load_user(user_id: str) -> dict:
    data = _read_data()
    return data.get(str(user_id), {})


def save_user(user_id: str, user_data: dict):
    data = _read_data()
    data[str(user_id)] = user_data
    _write_data(data)


def ensure_user(user_id: str, username: str = None) -> dict:
    data = _read_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "username": username or "",
            "created_at": datetime.utcnow().isoformat(),
            "has_used_paysafe": False,
            "transactions": [],
            "admin_flags": {
                "is_blocked": False,
                "requires_invoice": False
            }
        }
        _write_data(data)
    else:
        if "transactions" not in data[uid]:
            data[uid]["transactions"] = []
            _write_data(data)
    return data[uid]


def mark_paysafe_used(user_id: str):
    user = ensure_user(user_id)
    user["has_used_paysafe"] = True
    save_user(user_id, user)


def has_used_paysafe(user_id: str) -> bool:
    user = load_user(user_id)
    return user.get("has_used_paysafe", False)


def add_transaction(user_id: str, txn: dict):
    user = ensure_user(user_id)
    if "transactions" not in user:
        user["transactions"] = []
    user["transactions"].append({
        **txn,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_user(user_id, user)
