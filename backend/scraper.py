"""
Autonomous Scraper for Emirates Auction Live Inventory
Extracts live plate auction listings and persists directly into the SQLite comps database.
"""

import re
from datetime import datetime
from playwright.sync_api import sync_playwright

from database import db

def run_scraper():
    comps = []
    current_date = datetime.now().strftime("%b %Y")

    with sync_playwright() as p:
        print("Launching headless Chromium...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Navigating to Emirates Auction Live Inventory...")
        page.goto("https://www.emiratesauction.com/plates/uae-plates/online", wait_until="domcontentloaded")

        print("Waiting for inventory grid cards to render...")
        try:
            page.wait_for_selector('div[id^="CARD_PRICE_"]', timeout=20000)
        except Exception:
            print("Timeout waiting for CARD_PRICE elements. Attempting fallback locator scan.")

        cards = page.locator('div[id^="CARD_PRICE_"]').all()
        print(f"Found {len(cards)} live auction cards on page.")

        for card in cards:
            try:
                img_locator = card.locator('img[src*="/PLATES/"]').first
                price_locator = card.locator('span.safari-weight-500').first

                if img_locator.count() > 0 and price_locator.count() > 0:
                    img_src = img_locator.get_attribute('src') or ""
                    price_text = price_locator.inner_text()

                    # Robust regex extraction of plate code and number from CDN URL
                    match = re.search(r'/PLATES/([^/]+)/([0-9]+)\.png', img_src, re.IGNORECASE)
                    if match:
                        code = match.group(1).upper()
                        num = match.group(2)
                    else:
                        parts = img_src.split('/')
                        if len(parts) < 2:
                            continue
                        code = parts[-2].upper()
                        num = parts[-1].replace('.png', '').split('?')[0]
                        if not num.isdigit():
                            continue

                    clean_price = re.sub(r'[^\d]', '', price_text)
                    if not clean_price:
                        continue
                    price = int(clean_price)
                    digit_count = len(num)

                    plate_display = f"DUBAI {code} {num}"

                    comps.append({
                        "emirate": "dubai",
                        "digit_count": digit_count,
                        "plate": plate_display,
                        "price_aed": price,
                        "date": current_date,
                        "source": "Emirates Auction Live"
                    })
            except Exception:
                continue

        browser.close()

    if comps:
        inserted = db.insert_comps(comps)
        print(f"Pipeline complete: Scraped {len(comps)} live market comps. Newly inserted into SQLite: {inserted}. Total in DB: {db.count_comps()}.")
    else:
        print("No market comps found during scan.")

if __name__ == "__main__":
    run_scraper()
