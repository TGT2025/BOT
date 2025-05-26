# web/paysafe_locator.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def find_paysafecard_locations(postcode):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920x1080")

    try:
        driver = webdriver.Chrome(options=chrome_options)

        url = "https://www.paysafecard.com/en-gb/find-sales-outlet-1/"
        driver.get(url)

        # Accept cookies if popup appears
        try:
            accept_cookies = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All Cookies')]"))
            )
            accept_cookies.click()
            time.sleep(2)
        except:
            pass  # No cookies popup

        # Enter postcode
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "storelocator-email-input"))
        )
        search_box.clear()
        search_box.send_keys(postcode)
        search_box.send_keys(Keys.RETURN)

        # ✅ Wait longer for slow result loading
        time.sleep(10)

        store_names = driver.find_elements(By.CLASS_NAME, "display-2")
        store_addresses = driver.find_elements(By.CLASS_NAME, "sales-outlet__text")

        if not store_names or not store_addresses:
            return "❌ No Paysafecard locations found for this postcode."

        results = []
        for name, address in zip(store_names, store_addresses):
            try:
                store_name = name.text.strip()
                store_address = address.text.strip()
                results.append(f"🏪 {store_name}\n📍 {store_address}")
            except:
                continue

        return "\n\n".join(results[:5])  # Return top 5 only

    except Exception as e:
        return f"❌ Failed to fetch store locations. You can still purchase online.\n\nError: {str(e)}"
    finally:
        try:
            driver.quit()
        except:
            pass
