# state.py

# Global runtime state shared across modules
sessions = {}           # user_id -> current state
user_order_map = {}     # order_id -> user_id
