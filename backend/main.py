from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="UAE Plate Valuation Engine")

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

HISTORICAL_AUCTION_RECORDS = {
    ("dubai", 1): [
        {"plate": "DUBAI P 7", "price_aed": 55_000_000, "date": "Apr 2023", "source": "Most Noble Numbers"},
        {"plate": "DUBAI AA 9", "price_aed": 38_000_000, "date": "Apr 2021", "source": "Most Noble Numbers"},
    ],
    ("dubai", 2): [
        {"plate": "DUBAI AA 70", "price_aed": 3_820_000, "date": "May 2022", "source": "RTA Auction 110"},
        {"plate": "DUBAI V 99", "price_aed": 4_100_000, "date": "Dec 2023", "source": "RTA Auction 114"},
    ],
    ("dubai", 3): [
        {"plate": "DUBAI W 333", "price_aed": 720_000, "date": "Mar 2023", "source": "RTA Auction 112"},
        {"plate": "DUBAI Q 777", "price_aed": 850_000, "date": "Oct 2023", "source": "RTA Auction 113"},
    ],
    ("dubai", 4): [
        {"plate": "DUBAI X 1000", "price_aed": 195_000, "date": "Feb 2024", "source": "RTA Online Auction"},
        {"plate": "DUBAI Z 9999", "price_aed": 210_000, "date": "Dec 2023", "source": "RTA Online Auction"},
    ],
    ("dubai", 5): [
        {"plate": "DUBAI O 11111", "price_aed": 140_000, "date": "Jan 2024", "source": "RTA Online Auction"},
        {"plate": "DUBAI S 50000", "price_aed": 75_000, "date": "Mar 2024", "source": "RTA Online Auction"},
    ],
    ("abu dhabi", 1): [
        {"plate": "ABU DHABI 2", "price_aed": 23_300_000, "date": "Nov 2021", "source": "Emirates Auction"},
        {"plate": "ABU DHABI 5", "price_aed": 25_200_000, "date": "Nov 2020", "source": "Emirates Auction"},
    ],
    ("abu dhabi", 2): [
        {"plate": "ABU DHABI CAT 1 77", "price_aed": 9_150_000, "date": "Jun 2023", "source": "Emirates Auction"},
        {"plate": "ABU DHABI CAT 50 11", "price_aed": 4_600_000, "date": "Dec 2022", "source": "Emirates Auction"},
    ],
    ("abu dhabi", 3): [
        {"plate": "ABU DHABI CAT 1 111", "price_aed": 1_100_000, "date": "Mar 2023", "source": "Emirates Auction"},
        {"plate": "ABU DHABI CAT 4 500", "price_aed": 340_000, "date": "Oct 2023", "source": "Emirates Auction"},
    ],
    ("abu dhabi", 4): [
        {"plate": "ABU DHABI CAT 50 7777", "price_aed": 260_000, "date": "Nov 2023", "source": "Emirates Auction"},
        {"plate": "ABU DHABI CAT 1 1234", "price_aed": 180_000, "date": "Jan 2024", "source": "Emirates Auction"},
    ],
    ("abu dhabi", 5): [
        {"plate": "ABU DHABI CAT 1 98989", "price_aed": 92_000, "date": "Feb 2024", "source": "Emirates Auction"},
        {"plate": "ABU DHABI CAT 50 55555", "price_aed": 165_000, "date": "May 2023", "source": "Emirates Auction"},
    ],
}

def extract_patterns(num_str: str) -> tuple[list[str], float]:
    patterns = []
    multiplier = 1.0
    length = len(num_str)

    # 1. Cultural and National Landmarks
    if num_str == "786":
        patterns.append("Cultural Premium (786)")
        multiplier *= 4.5
    elif num_str == "1971":
        patterns.append("National Year (1971)")
        multiplier *= 8.0
    elif num_str == "2020":
        patterns.append("Expo Year (2020)")
        multiplier *= 3.0

    # 2. Mathematical Patterns
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

    # 3. Model and Sub-cultural Badges
    if num_str in CAR_BADGES:
        patterns.append("Automotive Model Match")
        multiplier *= 2.0

    if ("71" in num_str or num_str == "50") and "National Year (1971)" not in patterns:
        patterns.append("National Match")
        multiplier *= 1.35

    return patterns, multiplier

@app.post("/v1/evaluate", response_model=PlateResponse)
def evaluate_plate(payload: PlateRequest):
    num = payload.number.strip()
    raw_code = payload.code.strip().upper()
    emirate_clean = payload.emirate.strip().lower()

    if not num.isdigit() or not (1 <= len(num) <= 5):
        raise HTTPException(status_code=400, detail="Plate number must be between 1 and 5 digits.")

    # Code-level pricing calculations
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
        
        # Single-letter and double-letter matching premiums
        if len(raw_code) == 1:
            code_multiplier = 1.30
        elif len(raw_code) == 2 and raw_code[0] == raw_code[1]:
            code_multiplier = 1.45  # Matching pair (e.g., AA, RR, SS)
        else:
            code_multiplier = 1.0
        display_code = raw_code

    emirate_factor = EMIRATE_MULTIPLIERS.get(emirate_clean, 1.0)
    length = len(num)
    patterns, pattern_multiplier = extract_patterns(num)

    # Base pricing model
    if length == 1:
        base_val = 15_000_000
        calculated_fair = int(base_val * emirate_factor * pattern_multiplier * code_multiplier)
    elif length == 2:
        base_val = 1_150_000
        calculated_fair = int(base_val * emirate_factor * pattern_multiplier * code_multiplier)
    elif length == 3:
        base_val = 190_000
        calculated_fair = int(base_val * emirate_factor * pattern_multiplier * code_multiplier)
    elif length == 4:
        # Standard unpatterned 4-digits trade at standard entry baseline
        base_val = 5_000 if not patterns else 18_000
        calculated_fair = int(base_val * emirate_factor * pattern_multiplier * code_multiplier)
    else:  # 5 digits
        if not patterns:
            calculated_fair = 0
        else:
            base_val = 12_000
            calculated_fair = int(base_val * emirate_factor * pattern_multiplier * code_multiplier)

    if calculated_fair == 0:
        liquidation = 0
        dealer_ask = 0
        display_patterns = ["Standard Issue (No Market Premium)"]
        confidence = 0.99
    else:
        liquidation = int(calculated_fair * 0.78)
        dealer_ask = int(calculated_fair * 1.25)
        display_patterns = patterns if patterns else ["Standard Baseline Sequence"]
        confidence = 0.93 if patterns else 0.82

    matched_comps = [
        AuctionComp(**c)
        for c in HISTORICAL_AUCTION_RECORDS.get((emirate_clean, length), [])
    ]

    return PlateResponse(
        plate_display=f"{payload.emirate.upper()} {display_code} {num}",
        digit_count=length,
        patterns=display_patterns,
        liquidation_value_aed=liquidation,
        fair_market_value_aed=calculated_fair,
        dealer_ask_aed=dealer_ask,
        confidence_score=confidence,
        comps=matched_comps,
    )
