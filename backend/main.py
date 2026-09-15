import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_FILE = "auctions.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS auction_comps")
    cursor.execute("""
        CREATE TABLE auction_comps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emirate TEXT NOT NULL,
            digit_count INTEGER NOT NULL,
            plate TEXT NOT NULL,
            price_aed INTEGER NOT NULL,
            date TEXT NOT NULL,
            source TEXT NOT NULL
        )
    """)
    
    seed_data = [
        ("dubai", 1, "DUBAI P 7", 55000000, "Apr 2023", "Most Noble Numbers"),
        ("dubai", 1, "DUBAI AA 9", 38000000, "Apr 2021", "Most Noble Numbers"),
        ("dubai", 1, "DUBAI AA 8", 35000000, "Apr 2022", "Most Noble Numbers"),
        ("abu dhabi", 1, "ABU DHABI 2", 23300000, "Nov 2021", "Emirates Auction"),
        ("abu dhabi", 1, "ABU DHABI 5", 25200000, "Nov 2020", "Emirates Auction"),
        ("dubai", 2, "DUBAI AA 70", 3820000, "May 2022", "RTA Auction 110"),
        ("dubai", 2, "DUBAI V 99", 4100000, "Dec 2023", "RTA Auction 114"),
        ("dubai", 2, "DUBAI W 12", 2700000, "Sep 2023", "RTA Auction 113"),
        ("abu dhabi", 2, "ABU DHABI CAT 1 77", 9150000, "Jun 2023", "Emirates Auction"),
        ("abu dhabi", 2, "ABU DHABI CAT 50 11", 4600000, "Dec 2022", "Emirates Auction"),
        ("abu dhabi", 2, "ABU DHABI CAT 4 22", 3100000, "Feb 2024", "Emirates Auction"),
        ("dubai", 3, "DUBAI W 333", 720000, "Mar 2023", "RTA Auction 112"),
        ("dubai", 3, "DUBAI Q 777", 850000, "Oct 2023", "RTA Auction 113"),
        ("dubai", 3, "DUBAI J 1971", 1250000, "Nov 2022", "RTA Auction 111"),
        ("dubai", 3, "DUBAI Z 786", 620000, "Jan 2024", "RTA Special Auction"),
        ("abu dhabi", 3, "ABU DHABI CAT 1 111", 1100000, "Mar 2023", "Emirates Auction"),
        ("abu dhabi", 3, "ABU DHABI CAT 4 500", 340000, "Oct 2023", "Emirates Auction"),
        ("abu dhabi", 3, "ABU DHABI CAT 50 999", 780000, "Dec 2023", "Emirates Auction"),
        ("dubai", 4, "DUBAI X 1000", 195000, "Feb 2024", "RTA Online Auction"),
        ("dubai", 4, "DUBAI Z 9999", 210000, "Dec 2023", "RTA Online Auction"),
        ("dubai", 4, "DUBAI AA 1212", 185000, "Jan 2024", "RTA Online Auction"),
        ("abu dhabi", 4, "ABU DHABI CAT 50 7777", 260000, "Nov 2023", "Emirates Auction"),
        ("abu dhabi", 4, "ABU DHABI CAT 1 1234", 180000, "Jan 2024", "Emirates Auction"),
        ("abu dhabi", 4, "ABU DHABI CAT 4 8080", 95000, "Feb 2024", "Emirates Auction"),
        ("dubai", 5, "DUBAI O 11111", 140000, "Jan 2024", "RTA Online Auction"),
        ("dubai", 5, "DUBAI S 50000", 75000, "Mar 2024", "RTA Online Auction"),
        ("dubai", 5, "DUBAI R 91191", 42000, "Feb 2024", "RTA Online Auction"),
        ("dubai", 5, "DUBAI K 45892", 5200, "Mar 2024", "Dubizzle Verified"),
        ("abu dhabi", 5, "ABU DHABI CAT 50 55555", 165000, "May 2023", "Emirates Auction"),
        ("abu dhabi", 5, "ABU DHABI CAT 1 98989", 92000, "Feb 2024", "Emirates Auction"),
        ("abu dhabi", 5, "ABU DHABI CAT 4 10000", 85000, "Dec 2023", "Emirates Auction"),
    ]
    cursor.executemany(
        "INSERT INTO auction_comps (emirate, digit_count, plate, price_aed, date, source) VALUES (?, ?, ?, ?, ?, ?)",
        seed_data
    )
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="UAE Plate Valuation Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlateRequest(BaseModel):
    emirate: str = Field(..., example="Dubai")
    code: str = Field(..., example="A")
    number: str = Field(..., example="333")

class AuctionComp(BaseModel):
    plate: str
    price_aed: int
    date: str
    source: str

class PlateResponse(BaseModel):
    plate_display: str
    digit_count: int
    patterns: list[str]
    liquidation_value_aed: int
    fair_market_value_aed: int
    dealer_ask_aed: int
    confidence_score: float
    comps: list[AuctionComp]

EMIRATE_MULTIPLIERS = {
    "dubai": 1.25,
    "abu dhabi": 1.30,
    "sharjah": 0.85,
    "ajman": 0.65,
    "ras al khaimah": 0.60,
    "fujairah": 0.55,
    "umm al quwain": 0.50,
}

CAR_BADGES = {"911", "488", "720", "812", "300", "500", "63", "55", "718", "918", "296", "800", "700"}

def extract_patterns(num_str: str) -> tuple[list[str], float]:
    patterns = []
    multiplier = 1.0
    length = len(num_str)

    if num_str == "786":
        patterns.append("Cultural Premium (786)")
        multiplier *= 4.5
    elif num_str == "1971":
        patterns.append("National Year (1971)")
        multiplier *= 8.0
    elif num_str == "2020":
        patterns.append("Expo Year (2020)")
        multiplier *= 3.0

    if len(set(num_str)) == 1:
        patterns.append("Solid Repeater")
        multiplier *= 6.0
    elif num_str in "0123456789" or num_str in "9876543210":
        patterns.append("Sequential Sequence")
        multiplier *= 3.5
    elif length in [4, 5] and num_str == (num_str[:2] * 3)[:length]:
        patterns.append("Alternating Binary")
        multiplier *= 3.0
    elif num_str == num_str[::-1] and length > 2:
        patterns.append("Radar / Palindrome")
        multiplier *= 2.3
    elif length == 4 and num_str[:2] == num_str[2:]:
        patterns.append("Repeating Pair (ABAB)")
        multiplier *= 2.8
    elif length == 4 and (num_str[1:] == num_str[1] * 3 or num_str[:3] == num_str[0] * 3):
        patterns.append("Bookend Triplet")
        multiplier *= 2.2
    elif num_str[1:] == "0" * (length - 1):
        patterns.append("Clean Round Base")
        multiplier *= 2.5

    if num_str in CAR_BADGES:
        patterns.append("Automotive Model Match")
        multiplier *= 2.0

    if ("71" in num_str or num_str == "50") and "National Year (1971)" not in patterns:
        patterns.append("National Match")
        multiplier *= 1.35

    return patterns, multiplier

def fetch_nearest_comps(emirate: str, length: int, target_price: int, limit: int = 3) -> list[AuctionComp]:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT plate, price_aed, date, source
        FROM auction_comps
        WHERE emirate = ? AND digit_count = ?
        ORDER BY ABS(price_aed - ?) ASC
        LIMIT ?
    """, (emirate, length, target_price, limit))
    rows = cursor.fetchall()
    
    if not rows:
        cursor.execute("""
            SELECT plate, price_aed, date, source
            FROM auction_comps
            WHERE emirate = ?
            ORDER BY ABS(price_aed - ?) ASC
            LIMIT ?
        """, (emirate, target_price, limit))
        rows = cursor.fetchall()
        
    conn.close()
    return [AuctionComp(plate=r[0], price_aed=r[1], date=r[2], source=r[3]) for r in rows]

def fetch_exact_match(plate_display: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT price_aed FROM auction_comps WHERE plate = ?", (plate_display,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

@app.post("/v1/evaluate", response_model=PlateResponse)
def evaluate_plate(payload: PlateRequest):
    num = payload.number.strip()
    raw_code = payload.code.strip().upper()
    emirate_clean = payload.emirate.strip().lower()

    if not num.isdigit() or not (1 <= len(num) <= 5):
        raise HTTPException(status_code=400, detail="Plate number must be between 1 and 5 digits.")

    if emirate_clean == "abu dhabi":
        if not raw_code.isdigit():
            raise HTTPException(status_code=400, detail="Abu Dhabi plates require a numeric Category.")
        category_num = int(raw_code)
        if category_num == 1:
            code_multiplier = 1.85
        elif category_num in {2, 3, 4}:
            code_multiplier = 1.30
        elif category_num == 50:
            code_multiplier = 1.40
        else:
            code_multiplier = 1.0
        display_code = f"CAT {raw_code}"
    else:
        if not raw_code.isalpha() or not (1 <= len(raw_code) <= 2):
            raise HTTPException(status_code=400, detail=f"{payload.emirate} requires 1 or 2 letter codes.")
        if len(raw_code) == 1:
            code_multiplier = 1.30
        elif len(raw_code) == 2 and raw_code[0] == raw_code[1]:
            code_multiplier = 1.45
        else:
            code_multiplier = 1.0
        display_code = raw_code

    plate_display = f"{payload.emirate.upper()} {display_code} {num}"
    emirate_factor = EMIRATE_MULTIPLIERS.get(emirate_clean, 1.0)
    length = len(num)
    patterns, pattern_multiplier = extract_patterns(num)

    if length == 1:
        base_val = 15_000_000
    elif length == 2:
        base_val = 1_150_000
    elif length == 3:
        base_val = 190_000
    elif length == 4:
        base_val = 5_000 if not patterns else 18_000
    else:  
        base_val = 0 if not patterns else 12_000

    calculated_fair = int(base_val * emirate_factor * pattern_multiplier * code_multiplier)
    confidence = 0.93 if patterns else 0.82
    display_patterns = patterns if patterns else ["Standard Baseline Sequence"]

    exact_price = fetch_exact_match(plate_display)
    if exact_price:
        calculated_fair = exact_price
        display_patterns.append("Exact Auction Comp")
        confidence = 0.99
    elif calculated_fair == 0:
        display_patterns = ["Standard Issue (No Market Premium)"]
        confidence = 0.99

    if calculated_fair == 0:
        liquidation = 0
        dealer_ask = 0
    else:
        liquidation = int(calculated_fair * 0.78)
        dealer_ask = int(calculated_fair * 1.25)

    matched_comps = fetch_nearest_comps(emirate_clean, length, calculated_fair, limit=3)

    return PlateResponse(
        plate_display=plate_display,
        digit_count=length,
        patterns=display_patterns,
        liquidation_value_aed=liquidation,
        fair_market_value_aed=calculated_fair,
        dealer_ask_aed=dealer_ask,
        confidence_score=confidence,
        comps=matched_comps,
    )
