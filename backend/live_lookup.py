"""
Live Auction Lookup & On-Demand Inventory Verification
Probes live active auction listings across Emirates Auction and verified UAE sources.
"""

import time
import re
from typing import Optional, Dict, Any, List
from datetime import datetime

from database import db

# In-memory cache for live active auction listings to ensure sub-second response
_LIVE_INVENTORY_CACHE: Dict[str, Dict[str, Any]] = {}
_LAST_FETCH_TIME = 0.0
CACHE_TTL_SECONDS = 600.0  # 10 minutes cache freshness

def probe_live_auction_inventory() -> List[Dict[str, Any]]:
    """
    Executes a fast scan of current live active auction listings from Emirates Auction.
    Updates the in-memory cache and persists discovered plates directly into SQLite.
    """
    global _LIVE_INVENTORY_CACHE, _LAST_FETCH_TIME
    from playwright.sync_api import sync_playwright

    comps = []
    current_date = datetime.now().strftime("%b %Y")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto("https://www.emiratesauction.com/plates/uae-plates/online", wait_until="domcontentloaded", timeout=15000)
            try:
                page.wait_for_selector('div[id^="CARD_PRICE_"]', timeout=8000)
            except Exception:
                pass

            cards = page.locator('div[id^="CARD_PRICE_"]').all()
            for card in cards:
                try:
                    img_locator = card.locator('img[src*="/PLATES/"]').first
                    price_locator = card.locator('span.safari-weight-500').first

                    if img_locator.count() > 0 and price_locator.count() > 0:
                        img_src = img_locator.get_attribute('src') or ""
                        price_text = price_locator.inner_text()

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

                        record = {
                            "emirate": "dubai",
                            "code": code,
                            "number": num,
                            "digit_count": digit_count,
                            "plate": plate_display,
                            "price_aed": price,
                            "date": current_date,
                            "source": "Emirates Auction Live Active"
                        }
                        comps.append(record)
                        _LIVE_INVENTORY_CACHE[plate_display.upper()] = record
                except Exception:
                    continue

            browser.close()

        if comps:
            db.insert_comps(comps)
            _LAST_FETCH_TIME = time.time()
            print(f"Live auction scan successful: cached and inserted {len(comps)} active listings.")

    except Exception as e:
        print(f"Live auction scan encountered non-fatal error: {e}")

    return comps

def search_live_auction(emirate: str, code: str, number: str, allow_live_crawl: bool = False) -> Optional[Dict[str, Any]]:
    """
    Search live active auction inventory for a specific plate.
    1. Checks in-memory live inventory cache.
    2. If missing and allow_live_crawl is True, probes live auction website.
    3. If found, returns plate details and price; otherwise returns None.
    """
    plate_key = f"{emirate.strip().upper()} {code.strip().upper()} {number.strip()}"

    # 1. Check in-memory active cache
    if plate_key in _LIVE_INVENTORY_CACHE:
        return _LIVE_INVENTORY_CACHE[plate_key]

    # 2. Only probe live crawl if explicitly requested
    if allow_live_crawl:
        probe_live_auction_inventory()
        if plate_key in _LIVE_INVENTORY_CACHE:
            return _LIVE_INVENTORY_CACHE[plate_key]

    return None
