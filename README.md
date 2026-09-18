# UAE Plate Valuator: Market Intelligence Engine

A full-stack market intelligence platform designed to calculate the fair market value, liquidation value, and dealer ask price of UAE vehicle license plates. The engine combines heuristic pattern-recognition algorithms with a live, automated data pipeline scraping real-time auction data to anchor pricing models.

## System Architecture

* **Client / Frontend:** React Native (Expo)
* **API / Backend:** FastAPI (Python)
* **Database:** SQLite
* **Data Pipeline:** Playwright (Headless Chromium)
* **Deployment:** Render (Cloud Backend) / Expo EAS (Mobile Binaries)

## Core Components

### 1. Valuation Algorithm
UAE plate pricing is highly subjective, driven by cultural significance, digit repetition, and regional prestige. The engine utilizes a hybrid approach:
* **Heuristic Multipliers:** Base values are calculated using exponential decay for digit length (e.g., 2-digit plates hold exponentially higher base values than 5-digit plates) and premium multipliers for specific sequences (e.g., XYXY, XYZK). 
* **Market Anchoring:** Algorithmic outputs are cross-referenced and weighted against a localized SQLite database of verified transaction comps to prevent theoretical drift from actual market liquidity.

### 2. Automated Data Pipeline
Auction platforms utilize Single Page Application (SPA) architectures and continuous websocket polling to obscure inventory APIs and block standard HTTP scrapers. 
* A Python/Playwright headless scraper bypasses network-idle timeouts by interrogating the DOM after React lifecycle mounts.
* It extracts obscured plate configurations embedded within CDN image URLs, maps them against bid nodes, and injects clean, structured data into the SQLite comp database.

### 3. Fintech-Grade Client Interface
* **Monochromatic UI:** Deep black styling with high-contrast hierarchical typography and physical plate aspect-ratio rendering.
* **Local Edge Caching:** Implements `AsyncStorage` to persist recent search queries locally, eliminating redundant cloud API requests and nullifying layout-shift during load states.
* **Brokerage Deep-Linking:** Bypasses integrated payment gateways (due to UAE RTA regulatory restrictions on digital plate transfers) in favor of direct WhatsApp URL-scheme deep-linking for peer-to-peer lead generation.

## Local Development

**Backend API**
`cd backend`
`python -m venv venv`
`.\venv\Scripts\Activate.ps1`
`pip install fastapi uvicorn playwright`
`python scraper.py`
`uvicorn main:app --reload`

**Mobile Client**
`cd frontend`
`npm install`
`npx expo start`
