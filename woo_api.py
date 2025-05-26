import requests
import json
import uuid
from config import WC_API_URL, WC_CONSUMER_KEY, WC_CONSUMER_SECRET

def get_order_details(order_id):
    url = f"{WC_API_URL}/orders/{order_id}"
    response = requests.get(url, auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET))
    return response.json() if response.status_code == 200 else None

def issue_refund_coupon(order_total, paid_amount, customer_email):
    overpaid = round(paid_amount - order_total, 2)
    if overpaid <= 0:
        return None

    base_code = f"refund_{int(overpaid * 100)}p_{customer_email.split('@')[0]}".lower()
    code = base_code
    attempt = 1

    coupon_data = {
        "discount_type": "fixed_cart",
        "amount": f"{overpaid:.2f}",
        "individual_use": True,
        "description": f"Refund coupon for £{overpaid:.2f} - issued to {customer_email}",
        "usage_limit": 1
    }

    while attempt <= 5:
        coupon_data["code"] = code
        response = requests.post(
            f"{WC_API_URL}/coupons",
            auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
            json=coupon_data
        )
        if response.status_code == 201:
            return code  # ✅ Success
        elif response.status_code == 409:
            # Coupon already exists — try again with a new suffix
            code = f"{base_code}-{uuid.uuid4().hex[:4]}"
            attempt += 1
        else:
            break  # Some other failure

    return None  # ❌ All attempts failed

def find_tracking_number(postcode):
    try:
        with open("tracking_data.json", "r") as f:
            tracking_data = json.load(f)

        for record in tracking_data:
            if record.get("postcode", "").lower().replace(" ", "") == postcode.lower().replace(" ", ""):
                return record.get("tracking_number")
        return None
    except Exception:
        return None

# ==== ADDED FOR V1 LAUNCH ====

def update_order_status(order_id, new_status):
    """
    Update the WooCommerce order status.
    new_status can be: 'pending', 'processing', 'completed', etc.
    """
    url = f"{WC_API_URL}/orders/{order_id}"
    payload = {"status": new_status}

    response = requests.patch(
        url,
        auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
        json=payload
    )

    return response.status_code == 200
