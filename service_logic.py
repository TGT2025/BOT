# utils/service_logic.py

import os
import json
import re
import random
from datetime import datetime

# ✅ Fixed paths
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "client_service_history.json")
USAGE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "tier_service_usage.json")

print("📦 HISTORY_FILE:", HISTORY_FILE)
print("📦 USAGE_FILE:", USAGE_FILE)

FAKE_NAMES = [
    "Oscar Hay", "Ella Grant", "Liam Stone", "Chloe West", "Noah Field", "Ava Blake", "Leo Moore",
    "Maya Lane", "Ben Carter", "Ivy Brooks", "Jack Reid", "Nina Voss", "Tom Hale", "Anna Royce",
    "Luke Sharp", "Zoe Hart", "Evan Miles", "Ruby Faye", "Owen Nash", "Freya King"
]


SERVICE_MAPPING = [
    (150, 249.99, [
        {"code": "API", "name": "API Integration & Automation", "short": "API Integration", "detailed": "Integration of secure RESTful API endpoints to synchronize WooCommerce data with third-party platforms."},
        {"code": "ZAP", "name": "Zapier / Automation Setup", "short": "Workflow Automation", "detailed": "Automation of business processes using Zapier, Webhooks, and custom triggers."}
    ]),
    (250, 349.99, [
        {"code": "WOO", "name": "WooCommerce Store Setup", "short": "Store Setup", "detailed": "Full WooCommerce store setup with theme installation, plugin configuration, and payment setup."},
        {"code": "MIG", "name": "Shopify to Woo Migration", "short": "Migration", "detailed": "Migration of all products, customers, and order history from Shopify to WooCommerce."}
    ]),
    (350, 449.99, [
        {"code": "SEC", "name": "Security Audit & Compliance", "short": "Site Security Audit", "detailed": "Full security audit with vulnerability scanning, patching, and compliance verification."},
        {"code": "BAK", "name": "Backup & Recovery Plan", "short": "Recovery Setup", "detailed": "Setup of automated backups and recovery workflows using cloud services."}
    ]),
    (450, 549.99, [
        {"code": "PLG", "name": "Custom Plugin Development", "short": "Plugin Dev", "detailed": "Development of bespoke plugin solutions with scalable architecture and admin features."},
        {"code": "API2", "name": "API Microservice Creation", "short": "Microservice Dev", "detailed": "Design and deployment of secure, scalable microservices for Woo-based ecosystems."}
    ]),
    (550, 649.99, [
        {"code": "PAY", "name": "Payment Gateway Integration", "short": "Payment Setup", "detailed": "Integration of Stripe, PayPal, Klarna with secure token handling and live testing."},
        {"code": "SUB", "name": "Subscription System Setup", "short": "Subscriptions", "detailed": "Setup of Woo Subscriptions for recurring payments, renewals, and dunning."}
    ]),
    (650, 750.00, [
        {"code": "RET", "name": "Tech Support & Retainer", "short": "Retainer Services", "detailed": "Monthly technical support retainer including updates, optimization and uptime monitoring."},
        {"code": "OPS", "name": "DevOps Support Package", "short": "DevOps Support", "detailed": "CI/CD deployment setup, staging server, and pipeline configuration for WooCommerce."}
    ])
]

def clean_name(name):
    name = name.strip()
    if len(name) <= 3 or bool(re.match(r"^[A-Z][a-z]?\.?$", name)):
        return random.choice(FAKE_NAMES)
    return name.title()

def clean_address(address):
    return "\n".join([line for line in address.split("\n") if line.strip() and line.strip() != "GB"])

def get_client_history(email):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_client_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_usage():
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_usage(data):
    with open(USAGE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def select_service(client_email, order_total):
    usage_data = get_usage()
    for min_price, max_price, services in SERVICE_MAPPING:
        if min_price <= order_total <= max_price:
            tier_key = f"{min_price}-{max_price}"
            usage_data.setdefault(tier_key, {})
            tier_usage = usage_data[tier_key]

            # Sort services by fewest used
            services_sorted = sorted(services, key=lambda s: tier_usage.get(s["code"], 0))
            chosen = random.choice(services_sorted[:2])  # top 2 least-used → random realistic

            # Update usage
            tier_usage[chosen["code"]] = tier_usage.get(chosen["code"], 0) + 1
            save_usage(usage_data)
            return chosen

    return {
        "code": "GEN",
        "name": "General Consulting Services",
        "short": "Consulting Services",
        "detailed": "Professional consulting services tailored to your project needs."
    }

def update_client_history(email, code):
    history = get_client_history(email)
    if email not in history:
        history[email] = []
    history[email].append(code)
    save_client_history(history)
