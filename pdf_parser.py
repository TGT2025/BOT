# utils/pdf_parser.py

import pdfplumber
import re
from datetime import datetime

def extract_tracking_from_pdf(pdf_path):
    data = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                tracking_number = None
                postcode = None
                for line in lines:
                    match_tracking = re.search(r'([A-Z]{2}\s?\d{4}\s?\d{4}\s?\d{1,2}GB)', line)
                    if match_tracking:
                        tracking_number = match_tracking.group(1).replace(" ", "")
                    match_postcode = re.search(r'([A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2})$', line)
                    if match_postcode:
                        postcode = match_postcode.group(1).replace(" ", "").upper()
                if tracking_number and postcode:
                    data.setdefault(postcode, []).append({
                        "tracking": tracking_number,
                        "date": datetime.now().isoformat()
                    })
    return data
