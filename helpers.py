# ==== BATCH 1: REFERENCE CONSTANTS ====
import os
import json
import random
from datetime import datetime, timedelta
import pytz

WISE_REF_META = {
    "T2": [
        {"name": "Automation Support", "code": "AUT", "description": "Support for syncing smart devices, home assistants, and digital scheduling tools."},
        {"name": "Wi-Fi & Audio Visual", "code": "WAV", "description": "Advanced configuration of Wi-Fi networks and audio-visual systems for hybrid home environments."},
        {"name": "Home Tech Integration", "code": "HMT", "description": "Setup of user devices and automation tools to streamline home workflows and connectivity."}
    ],
    "T3": [
        {"name": "Home Wi-Fi Tuneup", "code": "HWT", "description": "Optimization of residential Wi-Fi networks, security, and signal performance enhancements."},
        {"name": "Connected Home Consultation", "code": "CHC", "description": "Consulting service for integrating smart home devices and custom automation solutions."}
    ],
    "T4": [
        {"name": "Private Tech Advisory", "code": "PRV", "description": "High-tier technical advisory and planning for bespoke home system setups."},
        {"name": "Private Installations Audit", "code": "PIA", "description": "Comprehensive audit and assessment of private technology installations, including networking and automation."}
    ]
}

REFERENCE_PREFIXES = ["VIP –", "Ride –", "XCL –", "Drv –", "Exec –", "Chf –"]
REFERENCE_SUFFIXES = ["– RT", "– FX", "– XR", "– D", "– P", "– LUX", "– DS", "– CHR"]

LOW_REF = ["Windsor", "Brighton", "Oxford", "Essex", "Cambridge",
    "Reading", "Guildford", "Maidstone", "Canterbury", "Basingstoke",
    "Swindon", "Milton Keynes", "Luton", "Chelmsford", "Colchester",
    "Hitchin", "Stevenage", "Chichester", "Southampton", "Bath"]

MID_REF = ["Essex-Gatwick", "Romford-Heathrow", "Lewes-Victoria", "Southend-London", "Croydon-Wharf",
    "Windsor-Paddington", "Oxford-Luton", "Clapham-Stansted", "Hounslow-Victoria", "Brighton-Central",
    "Luton-London", "Windsor-Gatwick", "Oxford-Heathrow", "Essex-City", "Lewisham-Gatwick",
    "Barking-KingsX", "Stratford-Oxford", "Deptford-Heathrow", "Ilford-Victoria", "Walthamstow-Central",
    "Harrow-Gatwick", "Camden-Stansted", "Chelsea-Luton", "Wembley-LHR", "Peckham-LCY"]

HIGH_REF = ["Mayfair Exec", "LDN-BTN RT", "West End Chauffeur", "Hove Exec", "Stratford VIP",
    "Oxford-Windsor Exec", "LHR-OXF VIP RT", "BTN-LUTON RT", "City–Gatwick Loop", "Windsor Full Day",
    "Oxford Exclusive", "LHR–Brighton VIP", "Chelsea Chauffeur", "Heathrow–Oxford–LDN", "BTN-VIP Day",
    "Essex Exec Tour", "Gatwick–Windsor Premium", "OXF–LDN RT", "Clapham Prestige", "Wembley Elite",
    "Mayfair-LHR Exec", "Knightsbridge VIP", "LDN-Cambridge RT", "OXF–BTN Chauffeur", "Soho Day Hire"]

ROUTES = ["Windsor-Heathrow", "Oxford-London", "Chelsea-Luton",
    "Southend-Victoria", "Brighton-Central", "Cambridge-Heathrow",
    "Luton-London", "Essex-City", "Clapham-Stansted"]

# ==== BATCH 2: LINK SCHEDULES ====
REVOLUT_LINK_SCHEDULE = {
    "M4W18": {
        "LCL": "https://checkout.revolut.com/pay/b0922ad1-7419-45a9-9687-4817a2d4c13c",
        "VIP": "https://checkout.revolut.com/pay/77615484-60a0-40be-b4eb-8101638f0286"
    },
    "M5W19": {
        "LCL": "https://checkout.revolut.com/pay/0c763de2-7124-4306-9dba-e28d7379bd94",
        "VIP": "https://checkout.revolut.com/pay/0930c118-f273-4140-ae3f-1dc444712be7"
    },
    "M5W20": {
        "LCL": "https://checkout.revolut.com/pay/1a44cb48-0889-4a1d-844a-5748c0185ad2",
        "VIP": "https://checkout.revolut.com/pay/85d81697-0ed0-4a91-a511-be63ea77e624"
    },
    "M5W21": {
        "LCL": "https://checkout.revolut.com/pay/f1ab93ae-9c0b-49aa-90ab-5653ecff3db5",
        "VIP": "https://checkout.revolut.com/pay/a75c3cf1-a44f-428d-9b84-29123275fc65"
    }
}

HIGH_VALUE_FALLBACKS = [
    "https://checkout.revolut.com/pay/a8a022cd-bc9f-4c49-99f2-073d3bd37bc0",
    "https://checkout.revolut.com/pay/53289671-94f5-4652-b3cc-7badc1852d84"
]

# ==== BATCH 3A: ARTISAN LINK SCHEDULES ====
REVOLUT_ARTISAN_SCHEDULE = {
    "ARTB1": {
        "market": [
            "https://checkout.revolut.com/pay/20ceb268-547c-4d1e-a72a-27db597fe49c"
        ],
        "private": [
            "https://checkout.revolut.com/pay/33dad93a-0d20-4b64-9fc1-a3a713bf3156"
        ]
    },
    "ARTB2": {
        "market": [
            "https://checkout.revolut.com/pay/5a1a03bb-329a-45a9-9625-df4f4b5e103a"
        ],
        "private": [
            "https://checkout.revolut.com/pay/eca052a3-3d2c-4013-85eb-bba7afeae551"
        ]
    },
    "ARTB3": {
        "market": [
            "https://checkout.revolut.com/pay/ea08a0fb-a558-4412-8a1a-d1897dd3051e"
        ],
        "private": [
            "https://checkout.revolut.com/pay/10dfaf67-46b5-4eb7-b95c-935c131f56ce"
        ]
    }
}


# ==== BATCH 3: ARTISAN STATIC REFERENCE SYSTEM ====
# ==== BATCH 3: ARTISAN STATIC REFERENCE SYSTEM ====
import os

ARTISAN_REFERENCE_TIERS = {
    "T1": [
        "ZLT-EARTH", "ZYT-OASIS", "YT-MEDINA", "ZLT-MIRAGE", "YT-ATLAS",
        "ZLD-OASIS", "ZYD-EARTH", "YD-MEDINA", "ZLD-ATLAS", "YD-PEBBLE"
    ],
    "T2": [
        "ZLG-NOOR", "ZLG-OASIS", "YG-ATLAS", "ZLG-MEDINA", "YG-RIAD"
    ],
    "T3": [
        "ZLF-MEDINA", "ZYF-OASIS", "YF-EARTH", "ZLF-ATLAS", "YF-MIRAGE"
    ],
    "T4": [
        "ZLP-ATLAS", "YP-RIAD", "ZYP-EARTH", "YP-NOOR", "ZLP-MEDINA"
    ]
}

ARTISAN_MARKET_DAYS = [3, 4, 5, 6]
ARTISAN_PRIVATE_DAYS = [0, 1, 2]

ARTISAN_PAYMENT_COUNTER_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "artisan_payment_counter.json")

def get_current_artisan_code():
    start_date = datetime(2025, 4, 20)
    today = datetime.now()
    days_passed = (today - start_date).days
    index = days_passed // 14
    return f"ARTB{index + 1}"

def get_static_artisan_reference(order_total):
    if order_total < 150:
        tier = "T1"
    elif order_total < 350:
        tier = "T2"
    elif order_total < 500:
        tier = "T3"
    else:
        tier = "T4"
    return random.choice(ARTISAN_REFERENCE_TIERS[tier])

def artisan_time_allowed():
    now = datetime.now(pytz.timezone("Europe/London"))
    return 5 <= now.hour < 23

def load_artisan_payment_counter():
    if os.path.exists(ARTISAN_PAYMENT_COUNTER_FILE):
        with open(ARTISAN_PAYMENT_COUNTER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_artisan_payment_counter(counter):
    with open(ARTISAN_PAYMENT_COUNTER_FILE, "w") as f:
        json.dump(counter, f, indent=2)

def artisan_daily_limit_ok():
    counter = load_artisan_payment_counter()
    today = datetime.now(pytz.timezone("Europe/London")).strftime("%Y-%m-%d")
    return counter.get(today, 0) < 8

def record_artisan_payment():
    counter = load_artisan_payment_counter()
    today = datetime.now(pytz.timezone("Europe/London")).strftime("%Y-%m-%d")
    counter[today] = counter.get(today, 0) + 1
    save_artisan_payment_counter(counter)

def get_revolut_artisan(order_total, link_type):
    if not artisan_time_allowed():
        raise ValueError("Artisan payments allowed only between 5AM and 11PM.")

    code = get_current_artisan_code()
    link_pool = REVOLUT_ARTISAN_SCHEDULE.get(code, {}).get(link_type, [])

    if not link_pool:
        for fallback_code in sorted(REVOLUT_ARTISAN_SCHEDULE.keys(), reverse=True):
            links = REVOLUT_ARTISAN_SCHEDULE[fallback_code].get(link_type, [])
            if links:
                link_pool = links
                print(f"[ARTISAN] Fallback to {fallback_code} for {link_type}")
                break

    if not link_pool:
        raise ValueError(f"[ARTISAN] No valid Revolut link for {link_type}")

    link = random.choice(link_pool)
    reference = get_static_artisan_reference(order_total)

    record_artisan_payment()

    return {
        "type": "revolut_artisan",
        "holder": "Revolut - Youssef El Osrouti",
        "reference": reference,
        "link": link
    }

# ==== CONTINUED (BATCH 4 & 5 NEXT) ====

# ==== BATCH 4: WEEK CODES & REFERENCES ====
def get_current_week_code():
    uk_time = datetime.now(pytz.timezone("Europe/London"))
    week = uk_time.isocalendar()[1]
    month = uk_time.month
    return f"M{month}W{week}"

def get_current_artisan_code():
    start_date = datetime(2025, 4, 20)
    today = datetime.now()
    days_passed = (today - start_date).days
    index = days_passed // 14
    return f"ARTB{index + 1}"

# ==== BATCH 5: MAIN PAYMENT ACCOUNT FUNCTIONS ====
# ==== BATCH 5: MAIN PAYMENT ACCOUNT FUNCTIONS ====

class WiseNotAvailable(Exception):
    pass

WISE_USAGE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "payment_rotation_tracker.json")
ROTATION_ORDER = ["revolut2", "revolut1", "wise"]

def wise_time_allowed():
    now = datetime.now(pytz.timezone("Europe/London"))
    return now.weekday() != 6 and 6 <= now.hour < 21  # Not Sunday, 6AM–9PM

def get_today_key():
    return datetime.now(pytz.timezone("Europe/London")).strftime("%Y-%m-%d")

def load_rotation_state():
    if os.path.exists(WISE_USAGE_FILE):
        with open(WISE_USAGE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_rotation_state(data):
    with open(WISE_USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_payment_account(order_total):
    data = load_rotation_state()
    today = get_today_key()

    if today not in data:
        data[today] = {
            "rotation_index": 0,
            "forced_wise_used": False,
            "wise_missed": False
        }

    state = data[today]

    # First eligible payment over £95 should go to Wise
    if order_total >= 95 and wise_time_allowed() and not state["forced_wise_used"]:
        state["forced_wise_used"] = True
        save_rotation_state(data)
        return get_wise_account()

    # Wise was skipped earlier, now eligible again → priority reroute
    if state["wise_missed"] and order_total >= 95 and wise_time_allowed():
        state["wise_missed"] = False
        save_rotation_state(data)
        return get_wise_account()

    # Rotation logic
    for _ in range(len(ROTATION_ORDER)):
        method = ROTATION_ORDER[state["rotation_index"]]
        state["rotation_index"] = (state["rotation_index"] + 1) % len(ROTATION_ORDER)

        if method == "wise":
            if order_total >= 95 and wise_time_allowed():
                save_rotation_state(data)
                return get_wise_account()
            else:
                state["wise_missed"] = True
                continue

        elif method == "revolut1":
            save_rotation_state(data)
            return get_revolut_account(order_total)

        elif method == "revolut2":
            save_rotation_state(data)
            return get_revolut_account(order_total)

    # Fallback in case all fail (shouldn't happen)
    return get_revolut_account(order_total)

def get_revolut_account(order_total):
    if order_total > 350:
        ref = get_revolut_reference(order_total)
        link = random.choice(HIGH_VALUE_FALLBACKS)
        return {
            "type": "revolut",
            "holder": "Revolut - Pantelis Aslanidis",
            "reference": ref,
            "link": link
        }

    week_code = get_current_week_code()
    plan = "VIP" if order_total > 125 else "LCL"

    route = random.choice(ROUTES)
    prefix = random.choice(["VIP", "EXEC"]) if plan == "VIP" else "LCL"
    suffix = "RTN" if plan == "VIP" else "OW"
    reference = f"{prefix} – {route} – {suffix}"

    link = REVOLUT_LINK_SCHEDULE.get(week_code, {}).get(plan)

    if not link:
        def parse_week(wk):
            month = int(wk[1:wk.index('W')])
            week = int(wk[wk.index('W') + 1:])
            return month, week

        today_month, today_week = parse_week(week_code)

        valid_weeks = []
        for wk in REVOLUT_LINK_SCHEDULE.keys():
            month, week = parse_week(wk)
            if (month < today_month) or (month == today_month and week <= today_week):
                if plan in REVOLUT_LINK_SCHEDULE[wk]:
                    valid_weeks.append(wk)

        if valid_weeks:
            best_week = max(valid_weeks, key=lambda x: parse_week(x))
            link = REVOLUT_LINK_SCHEDULE[best_week][plan]
            print(f"[REVOLUT] Corrected fallback to {best_week} for plan {plan}")

    if not link:
        raise ValueError(f"[REVOLUT] No valid link available for plan '{plan}'")

    return {
        "type": "revolut",
        "holder": "Revolut - Pantelis Aslanidis",
        "reference": reference,
        "link": link
    }

def get_revolut_reference(order_total: float) -> str:
    prefix = random.choice(REFERENCE_PREFIXES)
    suffix = random.choice(REFERENCE_SUFFIXES)

    if order_total < 50:
        ref = random.choice(LOW_REF)
    elif order_total < 150:
        ref = random.choice(MID_REF)
    else:
        ref = random.choice(HIGH_REF)

    return f"{prefix}{ref}{suffix}"

def get_wise_reference(order_total):
    if order_total < 95 or not wise_time_allowed():
        raise WiseNotAvailable("Wise not available due to value or time")

    if order_total < 250:
        tier = "T2"
    elif order_total < 300:
        tier = "T3"
    else:
        tier = "T4"

    entry = random.choice(WISE_REF_META[tier])
    return f"{entry['name']} – {entry['code']}"

def get_wise_invoice_meta(order_total):
    if order_total < 95 or not wise_time_allowed():
        raise WiseNotAvailable("Wise not available due to value or time")

    if order_total < 250:
        tier = "T2"
    elif order_total < 300:
        tier = "T3"
    else:
        tier = "T4"

    return random.choice(WISE_REF_META[tier])

def get_wise_account():
    if not wise_time_allowed():
        raise WiseNotAvailable("Wise not available outside 6AM–8PM or on Sundays")

    return {
        "type": "wise",
        "holder": "Pinnacle UK Consulting Ltd",
        "reference": "Auto-generated per order",
        "bank_sort": "23-08-01",
        "bank_acc": "13877723"
    }
