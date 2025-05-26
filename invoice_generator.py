import os
import json
import re
import random
import pytz
from datetime import datetime
from fpdf import FPDF
import requests

from config import WC_API_URL, WC_CONSUMER_KEY, WC_CONSUMER_SECRET, OUTPUT_FOLDER, LOGO_PATH
from utils.helpers import get_wise_reference

# Ensure the output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

FAKE_NAMES = [
    "Oscar Hay", "Ella Grant", "Liam Stone", "Chloe West", "Noah Field", "Ava Blake", "Leo Moore",
    "Maya Lane", "Ben Carter", "Ivy Brooks", "Jack Reid", "Nina Voss", "Tom Hale", "Anna Royce",
    "Luke Sharp", "Zoe Hart", "Evan Miles", "Ruby Faye", "Owen Nash", "Freya King"
]

# === CLEANING FUNCTIONS ===
def clean_name(name):
    name = name.strip()
    if len(name) <= 3 or bool(re.match(r"^[A-Z][a-z]?\.?$", name)):
        return random.choice(FAKE_NAMES)
    return name.title()

def clean_address(address):
    return "\n".join([line for line in address.split("\n") if line.strip() and line.strip() != "GB"])

def format_uk_phone(phone):
    phone = re.sub(r"\D", "", phone)
    if phone.startswith("0"):
        return "+44 " + phone[1:]
    elif phone.startswith("44"):
        return "+" + phone
    elif phone.startswith("7"):
        return "+44 " + phone
    return phone

def pdf_safe(text):
    if not text:
        return ""
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "…": "...", "•": "*",
        "€": "EUR", "£": "GBP", "\u00a0": " "
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text.encode("latin-1", "ignore").decode("latin-1")

# === TIME WINDOW ===
def is_wise_time_window():
    now = datetime.now(pytz.timezone("Europe/London"))
    weekday = now.weekday()
    hour = now.hour
    return (weekday in range(0, 6) and 6 <= hour < 20)

# === WOO ===
def get_order_details(order_id):
    url = f"{WC_API_URL}/orders/{order_id}"
    response = requests.get(url, auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET))
    return response.json() if response.status_code == 200 else None

def generate_reference(service_code, client_name, sequence=1):
    if not service_code:
        service_code = "GEN"
    date_str = datetime.today().strftime('%Y%m%d')
    client_code = ''.join(client_name.upper().split())[:6] or "CLIENT"
    return f"{service_code}-{date_str}-{client_code}-{sequence:03d}"

# === PDF GENERATION ===
def create_invoice_pdf(ref, client, service_name, service_description, amount, client_phone, output_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    if os.path.exists(LOGO_PATH):
        try:
            pdf.image(LOGO_PATH, x=160, y=10, w=40)
        except RuntimeError as e:
            print(f"Error loading logo: {e}")

    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "INVOICE", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", size=11)
    pdf.cell(0, 6, "Pinnacle UK Consulting Ltd", ln=True)
    pdf.cell(0, 6, "Company No: 16287544", ln=True)
    pdf.cell(0, 6, "14 Box Ridge Avenue, Purley, CR8 3AP", ln=True)
    pdf.cell(0, 6, "Email: vestaschaphw@hotmail.com | Phone: +44 7494 468980", ln=True)
    pdf.ln(8)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, f"Invoice Reference: {ref}", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 6, f"Date: {datetime.today().strftime('%B %d, %Y')}", ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "Billed To:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 6, pdf_safe(client['name']), ln=True)
    for line in pdf_safe(client['address']).split("\n"):
        pdf.cell(0, 6, pdf_safe(line), ln=True)
    pdf.cell(0, 6, f"Email: {pdf_safe(client['email'])}", ln=True)
    pdf.cell(0, 6, f"Phone: {format_uk_phone(client_phone)}", ln=True)
    pdf.ln(6)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "Project Description:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 6, pdf_safe(service_name), ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "Service Details:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, pdf_safe(service_description))
    pdf.ln(6)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(140, 8, "Description", border=1)
    pdf.cell(50, 8, "Amount (GBP)", border=1, ln=True)

    pdf.set_font("Arial", size=11)
    pdf.cell(140, 8, pdf_safe(service_name), border=1)
    pdf.cell(50, 8, f"£{amount:.2f}", border=1, ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(140, 8, "TOTAL", border=1)
    pdf.cell(50, 8, f"£{amount:.2f}", border=1, ln=True)

    pdf.ln(6)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 5, pdf_safe(
        "Bank Transfer Details:\n"
        "Pinnacle UK Consulting Ltd\n"
        "Account No: 13877723\n"
        "Sort Code: 23-08-01\n"
        "Bank: Wise Business"
    ))

    pdf.set_y(-35)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 5, pdf_safe(
        "No VAT charged – business is not VAT registered.\n"
        "Thank you for your business. This invoice confirms payment has been received.\n"
        "Please retain it for your records.\n"
        "For any queries, contact: vestaschaphw@hotmail.com.\n"
        "This is a system-generated document."
    ))

    print(f"[PDF DEBUG] Writing invoice to: {output_path}")
    pdf.output(output_path)
    print(f"[PDF DEBUG] File written? {os.path.exists(output_path)}")

# === ENTRY POINT ===
def generate_invoice(order_id, reference, service_name, service_description):
    order = get_order_details(order_id)
    if not order:
        return None

    if not service_name or not service_description:
        raise ValueError("Missing service_name or service_description. Invoice cannot be generated.")

    client_name = clean_name(f"{order['billing']['first_name']} {order['billing']['last_name']}")
    client_email = order['billing']['email']
    client_phone = order['billing']['phone']
    client_address_raw = "\n".join(filter(None, [
        order['billing']['address_1'],
        order['billing']['address_2'],
        order['billing']['city'],
        order['billing']['postcode'],
        order['billing']['country']
    ]))
    client_address = clean_address(client_address_raw)
    amount = float(order['total'])

    output_file = os.path.join(OUTPUT_FOLDER, f"{reference}.pdf")
    create_invoice_pdf(reference, {
        "name": client_name,
        "email": client_email,
        "address": client_address
    }, service_name, service_description, amount, client_phone, output_file)

    return output_file
