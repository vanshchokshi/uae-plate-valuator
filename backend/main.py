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

BASE_BENCHMARKS = {
    1: 14_500_000,
    2: 1_250_000,
    3: 320_000,
    4: 60_000,
    5: 12_500,
}

CAR_BADGES = {"911", "488", "720", "812", "300", "500", "63", "55", "718", "918"}

HISTORICAL_AUCTION_RECORDS = {
    1: [
        {"plate": "DUBAI P 7", "price_aed": 55_000_000, "date": "Apr 2023", "source": "Most Noble Numbers"},
        {"plate": "DUBAI AA 9", "price_aed": 38_000_000, "date": "Apr 2021", "source": "Most Noble Numbers"},
        {"plate": "ABU DHABI 2", "price_aed": 23_300_000, "date": "Nov 2021", "source": "Emirates Auction"},
    ],
    2: [
        {"plate": "DUBAI AA 70", "price_aed": 3_820_000, "date": "May 2022", "source": "RTA Auction 110"},
        {"plate": "DUBAI V 99", "price_aed": 4_100_000, "date": "Dec 2023", "source": "RTA Auction 114"},
        {"plate": "ABU DHABI CAT 1 77", "price_aed": 9_150_000, "date": "Jun 2023", "source": "Emirates Auction"},
    ],
    3: [
        {"plate": "DUBAI W 333", "price_aed": 720_000, "date": "Mar 2023", "source": "RTA Auction 112"},
        {"plate": "DUBAI Q 777", "price_aed": 850_000, "date": "Oct 2023", "source": "RTA Auction 113"},
        {"plate": "SHARJAH 111", "price_aed": 610_000, "date": "Jan 2024", "source": "Sharjah Police Auction"},
    ],
    4: [
        {"plate": "DUBAI X 1000", "price_aed": 195_000, "date": "Feb 2024", "source": "RTA Online Auction"},
        {"plate": "ABU DHABI CAT 50 7777", "price_aed": 260_000, "date": "Nov 2023", "source": "Emirates Auction"},
        {"plate": "DUBAI Z 9999", "price_aed": 210_000, "date": "Dec 2023", "source": "RTA Online Auction"},
    ],
    5: [
        {"plate": "DUBAI O 11111", "price_aed": 140_000, "date": "Jan 2024", "source": "RTA Online Auction"},
        {"plate": "DUBAI S 50000", "price_aed": 75_000, "date": "Mar 2024", "source": "RTA Online Auction"},
        {"plate": "ABU DHABI CAT 1 98989", "price_aed": 92_000, "date": "Feb 2024", "source": "Emirates Auction"},
    ],
}

def extract_patterns(num_str: str) -> tuple[list[str], float]:
    patterns = []
    multiplier = 1.0
    length = len(num_str)

    if len(set(num_str)) == 1:
        patterns.append("Solid Repeater")
        multiplier *= 3.8
    elif num_str in "0123456789" or num_str in "9876543210":
        patterns.append("Sequential")
        multiplier *= 2.4
    elif num_str == num_str[::-1] and length > 2:
        patterns.append("Palindrome")
        multiplier *= 1.7
    elif length == 4 and num_str[:2] == num_str[2:]:
        patterns.append("Repeating Pair")
        multiplier *= 2.0
    elif num_str[1:] == "0" * (length - 1):
        patterns.append("Round Base")
        multiplier *= 1.6

    if num_str in CAR_BADGES:
        patterns.append("Automotive Model Match")
        multiplier *= 1.5

    if "71" in num_str or num_str == "50":
        patterns.append("National Year Match")
        multiplier *= 1.3

    return patterns, multiplier

@app.post("/v1/evaluate", response_model=PlateResponse)
def evaluate_plate(payload: PlateRequest):
    num = payload.number.strip()
    raw_code = payload.code.strip().upper()
    emirate_clean = payload.emirate.strip().lower()

    if not num.isdigit() or not (1 <= len(num) <= 5):
        raise HTTPException(status_code=400, detail="Plate number must be between 1 and 5 digits.")

    if emirate_clean == "abu dhabi":
        if not raw_code.isdigit():
            raise HTTPException(status_code=400, detail="Abu Dhabi plates require a numeric Category (e.g. 1, 4, 50).")
        category_num = int(raw_code)
        if category_num == 1:
            code_multiplier = 1.75
        elif category_num in {2, 3, 4}:
            code_multiplier = 1.25
        elif category_num == 50:
            code_multiplier = 1.35
        else:
            code_multiplier = 1.0
        display_code = f"CAT {raw_code}"
    else:
        if not raw_code.isalpha() or not (1 <= len(raw_code) <= 2):
            raise HTTPException(status_code=400, detail=f"{payload.emirate} requires 1 or 2 letter codes.")
        code_multiplier = 1.15 if len(raw_code) == 1 else 1.0
        display_code = raw_code

    emirate_factor = EMIRATE_MULTIPLIERS.get(emirate_clean, 1.0)
    length = len(num)
    base_val = BASE_BENCHMARKS.get(length, 10_000)

    patterns, pattern_multiplier = extract_patterns(num)
    calculated_fair = int(base_val * emirate_factor * pattern_multiplier * code_multiplier)

    matched_comps = [
        AuctionComp(
            plate=c["plate"],
            price_aed=c["price_aed"],
            date=c["date"],
            source=c["source"]
        )
        for c in HISTORICAL_AUCTION_RECORDS.get(length, [])
    ]

    return PlateResponse(
        plate_display=f"{payload.emirate.upper()} {display_code} {num}",
        digit_count=length,
        patterns=patterns if patterns else ["Standard Sequence"],
        liquidation_value_aed=int(calculated_fair * 0.78),
        fair_market_value_aed=calculated_fair,
        dealer_ask_aed=int(calculated_fair * 1.25),
        confidence_score=0.94 if patterns else 0.80,
        comps=matched_comps,
    )
