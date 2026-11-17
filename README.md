# UAE Plate Valuator: Multi-Source Market Intelligence Engine

A full-stack market intelligence platform designed to calculate the **Fair Market Value**, **Liquidation Value** (instant cash/pawn), and **Dealer Ask Price** (retail showroom) of UAE vehicle license plates. 

The engine cross-references across multiple verified tiers: **Dubai RTA Official Auctions**, **Emirates Auction (Abu Dhabi/Sharjah Police)**, and **Verified Dealerships (Dubizzle / Alain Class / Pearl Motors)** alongside heuristic pattern-recognition algorithms to anchor pricing models.

---

## Verified Market Data Sources

The platform implements a modular **Multi-Source Aggregator** (`backend/sources/`):

1. **Official Government Auctions (`official_government`)**:
   * **Dubai RTA Grand & Online Auctions**: Quarterly historical clearing prices (Auctions 105 through 115).
   * **"Most Noble Numbers" Royal Charity Auctions**: Benchmark world-record sales (e.g. `P 7` for 55M AED, `AA 9` for 38M AED).
2. **Authorized Auction Concessionaires (`concessionaire`)**:
   * **Emirates Auction**: Official contracted auctioneer for Abu Dhabi Police, Sharjah Police, Ras Al Khaimah, Fujairah, and Ajman courts.
   * Includes automated headless scraper pipeline for real-time live bid detection.
3. **Verified Dealer Marketplace (`dealer_marketplace`)**:
   * **Dubizzle Verified Transactions**: Active secondary market transactions.
   * **Licensed Luxury Showrooms**: Consignment showroom ask prices from Al Aweer and Sheikh Zayed Road (Alain Class Motors, Pearl Motors, Deals on Wheels, VIP Number Plates UAE).

---

## System Architecture

* **Client / Frontend:** React Native (Expo SDK 52+)
* **API / Backend:** FastAPI (Python 3.11+)
* **Database:** Embedded SQLite (`auctions.db`) with composite indexes on `(emirate, digit_count, price_aed)` and `(plate)`
* **Data Sources:** Multi-Source Provider Framework (`backend/sources/`)
* **Scraper Pipeline:** Playwright (Headless Chromium)
* **Agent Integration:** FastMCP Server (`mcp_server.py`)
* **CI/CD:** GitHub Actions (Automated testing & scraper pipeline)

---

## Core Components

### 1. Multi-Tier Valuation Engine
UAE plate pricing is driven by digit brevity, cultural significance, sequence repetition, and regional prestige:
* **Digit Length Exponential Decay:** 1-digit plates hold base valuations upwards of 15M AED down to standard 5-digit circulation.
* **Pattern Recognition:**
  * **Radars / Palindromes:** (e.g., `121`, `9119`, `12321`)
  * **Super Solids:** Repeating single digits (e.g., `77777`, `8888`, `333`)
  * **Repeating Pairs:** (e.g., `1212`, `5050`, `7070`)
  * **Consecutive Sequences:** (e.g., `123`, `1234`, `12345`)
  * **Clean Round Bases:** (e.g., `1000`, `20000`, `50000`)
  * **Cultural & National Match:** `786` (Bismillah cultural premium), `1971` (UAE Year of Federation), `50` (Golden Jubilee)
  * **Automotive Model Matches:** `911`, `488`, `720`, `812`, `63`, `55`, etc.
* **Emirate & Code Multipliers:** Weighted factors across Dubai, Abu Dhabi (Categories 1, 2, 50), Sharjah, and Northern Emirates.
* **Multi-Source Market Anchoring:** Algorithmic outputs are cross-referenced against historical auction transactions to anchor pricing to verified real-world comps.

### 2. High-Performance Embedded Database (SQLite)
* Self-contained in `backend/auctions.db`.
* Zero external cloud services, API tokens, or setup required. Pre-seeded with 100+ verified UAE auction and dealership benchmarks across Dubai, Abu Dhabi, and Sharjah.
* Sub-millisecond query response time (< 1ms).

### 3. Automated Data Pipeline & Scraper
* Headless Chromium Playwright scraper crawls Emirates Auction live inventory.
* Bypasses client-rendered React mounting delays using dynamic DOM selectors and extracts plate codes and numbers directly from CDN image URLs, persisting directly into SQLite.

### 4. Client Interface (Expo React Native)
* **Monochromatic Dark UI:** Deep black styling with high-contrast hierarchical typography and physical plate preview.
* **Multi-Emirate Support:** One-tap toggle between Dubai, Abu Dhabi, and Sharjah.
* **Edge Caching:** `AsyncStorage` persists recent searches for instant 1-tap re-valuation.
* **Brokerage Deep-Linking:** Direct WhatsApp lead generation deep linking.
* **Live Crawl Toggle:** Optional on-demand live probe against active auction inventory.

---

## Local Development

### 1. Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

To run the API server:
```powershell
uvicorn main:app --reload --port 8000
```
Interactive API docs available at: `http://localhost:8000/docs`

To inspect connected market data sources:
```powershell
curl http://localhost:8000/v1/sources
```

To run the automated test suite:
```powershell
pytest
```

To run the autonomous scraper:
```powershell
python scraper.py
```

### 2. Mobile Client Setup
```powershell
cd frontend
npm install
npx expo start
```
* Press `w` to launch in the web browser.
* Press `a` or scan the QR code with Expo Go on your mobile device.

To configure a custom remote backend URL, create `frontend/.env`:
```env
EXPO_PUBLIC_API_URL=http://localhost:8000
```
