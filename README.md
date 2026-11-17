# UAE Plate Valuator: Market Intelligence Engine

A full-stack market intelligence platform designed to calculate the **Fair Market Value**, **Liquidation Value** (instant cash/pawn), and **Dealer Ask Price** (retail showroom) of UAE vehicle license plates. The engine combines heuristic pattern-recognition algorithms with a live automated data pipeline scraping real-time auction comps to anchor pricing models.

---

## System Architecture

* **Client / Frontend:** React Native (Expo SDK 52+)
* **API / Backend:** FastAPI (Python 3.11+)
* **Database:** Hybrid Architecture — Supabase (PostgreSQL Cloud) with automatic, zero-config fallback to local SQLite (`auctions.db`)
* **Data Pipeline:** Playwright (Headless Chromium)
* **Agent Integration:** FastMCP Server (`mcp_server.py`)
* **CI/CD:** GitHub Actions (Scraper automation & Pytest suite)

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
* **Market Anchoring:** Algorithmic outputs are cross-referenced against historical auction transactions to anchor pricing to verified real-world comps.

### 2. Dual Database (Cloud + Local Fallback)
* Automatically connects to **Supabase** when `SUPABASE_URL` and `SUPABASE_KEY` are provided.
* If unconfigured or offline, seamlessly falls back to a curated local **SQLite** database (`auctions.db`) seeded with benchmark UAE auction transactions. Zero setup required to run out of the box!

### 3. Automated Data Pipeline & Scraper
* Headless Chromium Playwright scraper crawls Emirates Auction live inventory.
* Bypasses client-rendered React mounting delays using dynamic DOM selectors and extracts plate codes and numbers directly from CDN image URLs.

### 4. Client Interface (Expo React Native)
* **Monochromatic Dark UI:** Deep black styling with high-contrast hierarchical typography and physical plate preview.
* **Multi-Emirate Support:** One-tap toggle between Dubai, Abu Dhabi, and Sharjah.
* **Edge Caching:** `AsyncStorage` persists recent searches for instant 1-tap re-valuation.
* **Brokerage Deep-Linking:** Direct WhatsApp lead generation deep linking.

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
