import sqlite3
from playwright.sync_api import sync_playwright
from datetime import datetime

DB_FILE = "auctions.db"

def insert_comps(comps):
    if not comps:
        print("No market comps found to extract.")
        return
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auction_comps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emirate TEXT,
            digit_count INTEGER,
            plate TEXT,
            price_aed INTEGER,
            date TEXT,
            source TEXT
        )
    """)
    
    cursor.executemany(
        "INSERT INTO auction_comps (emirate, digit_count, plate, price_aed, date, source) VALUES (?, ?, ?, ?, ?, ?)",
        comps
    )
    conn.commit()
    conn.close()
    print(f"Successfully scraped and inserted {len(comps)} live market comps into SQLite.")

def run_scraper():
    comps = []
    current_date = datetime.now().strftime("%b %Y")
    
    with sync_playwright() as p:
        print("Launching headless Chromium...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating to Emirates Auction Live Inventory...")
        page.goto("https://www.emiratesauction.com/plates/uae-plates/online", wait_until="domcontentloaded")
        
        print("Waiting 8 seconds for React to mount the inventory grid...")
        page.wait_for_timeout(8000)
        
        print("Extracting image paths and price nodes...")
        cards = page.locator('div[id^="CARD_PRICE_"]').all()
        
        for card in cards:
            try:
                img_locator = card.locator('img[src*="/PLATES/"]').first
                price_locator = card.locator('span.safari-weight-500').first
                
                if img_locator.count() > 0 and price_locator.count() > 0:
                    img_src = img_locator.get_attribute('src')
                    price_text = price_locator.inner_text()
                    
                    parts = img_src.split('/')
                    code = parts[-2].upper()
                    num = parts[-1].replace('.png', '')
                    
                    price = int(price_text.replace(',', '').strip())
                    digit_count = len(num)
                    
                    plate_display = f"DUBAI {code} {num}"
                    
                    comps.append(("dubai", digit_count, plate_display, price, current_date, "Emirates Auction Live"))
            except Exception:
                continue
        
        browser.close()
        insert_comps(comps)

if __name__ == "__main__":
    run_scraper()
