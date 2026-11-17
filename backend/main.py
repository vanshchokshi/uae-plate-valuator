import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from valuation import valuate
from database import db
from live_lookup import search_live_auction, probe_live_auction_inventory

app = FastAPI(
    title="UAE Plate Valuation Engine",
    description="Fintech-grade valuation engine with on-demand live auction verification and SQLite comps intelligence.",
    version="2.2.0"
)

# Open CORS configuration for Expo mobile and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlateRequest(BaseModel):
    emirate: str = Field(default="Dubai", json_schema_extra={"example": "Dubai"})
    code: str = Field(..., json_schema_extra={"example": "A"})
    number: str = Field(..., json_schema_extra={"example": "333"})
    check_live: bool = Field(default=False, description="Whether to probe live auction platforms if missing from DB")

class AuctionComp(BaseModel):
    plate: str
    price_aed: int
    date: str
    source: str

class PlateResponse(BaseModel):
    plate_display: str
    emirate: str
    code: str
    number: str
    digit_count: int
    patterns: List[str]
    fair_market_value_aed: int
    liquidation_value_aed: int
    dealer_ask_aed: int
    confidence_score: float
    comps: List[AuctionComp]
    is_live_listing: bool = False
    # Backward compatibility fields
    estimated_value: int
    comparable_count: int

@app.get("/health")
def health_check():
    """Health check endpoint reporting SQLite database metrics."""
    return {
        "status": "healthy",
        "database": "sqlite",
        "comps_in_db": db.count_comps()
    }

@app.post("/v1/live-sync")
def trigger_live_sync(background_tasks: BackgroundTasks):
    """
    Trigger an on-demand background scan of Emirates Auction live active inventory
    to discover and persist newly listed plates into the database.
    """
    background_tasks.add_task(probe_live_auction_inventory)
    return {"status": "Live auction synchronization initiated in background."}

@app.get("/comps")
@app.get("/v1/comps")
def get_comps(
    emirate: Optional[str] = Query(None, description="Optional filter by emirate (e.g. dubai, abu dhabi)"),
    limit: int = Query(50, ge=1, le=100)
):
    """Retrieve historical and live auction comparable records."""
    try:
        data = db.get_comps(emirate=emirate, limit=limit)
        return {"data": data, "count": len(data), "database": "sqlite"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve auction comps.")

@app.post("/v1/evaluate", response_model=PlateResponse)
def evaluate_plate(payload: PlateRequest):
    """
    Comprehensive valuation endpoint.
    1. Checks local SQLite DB for exact auction record.
    2. If missing, optionally probes live auction platforms (Emirates Auction).
    3. If not found on live platforms, runs the heuristic valuation engine.
    """
    num = payload.number.strip()
    raw_code = payload.code.strip()
    emirate = payload.emirate.strip()

    if not num.isdigit() or not (1 <= len(num) <= 5):
        raise HTTPException(status_code=400, detail="Plate number must be between 1 and 5 numeric digits.")

    if not raw_code:
        raise HTTPException(status_code=400, detail="Plate code or category is required.")

    temp_display = f"{emirate.upper()} {raw_code.upper()} {num}"
    is_live_listing = False

    # 1. Check local SQLite database for exact historical auction comp
    exact_price = db.fetch_exact_match(temp_display)

    # 2. If not found in DB, probe live auction inventory
    if not exact_price:
        live_result = search_live_auction(
            emirate=emirate,
            code=raw_code,
            number=num,
            allow_live_crawl=payload.check_live
        )
        if live_result:
            exact_price = live_result.get("price_aed")
            is_live_listing = True

    # 3. Run heuristic valuation engine
    valuation_data = valuate(
        emirate=emirate,
        code=raw_code,
        number=num,
        exact_comp_price=exact_price
    )

    display_patterns = list(valuation_data["patterns"])
    if is_live_listing:
        display_patterns.insert(0, "Emirates Auction Live Active Listing")

    # 4. Fetch nearest price comps
    matched_comps = db.fetch_nearest_comps(
        emirate=valuation_data["emirate"],
        digit_count=valuation_data["digit_count"],
        target_price=valuation_data["fair_market_value_aed"],
        limit=3
    )

    comp_models = [
        AuctionComp(
            plate=c["plate"],
            price_aed=c["price_aed"],
            date=c["date"],
            source=c["source"]
        )
        for c in matched_comps
    ]

    return PlateResponse(
        plate_display=valuation_data["plate_display"],
        emirate=valuation_data["emirate"],
        code=valuation_data["code"],
        number=valuation_data["number"],
        digit_count=valuation_data["digit_count"],
        patterns=display_patterns,
        fair_market_value_aed=valuation_data["fair_market_value_aed"],
        liquidation_value_aed=valuation_data["liquidation_value_aed"],
        dealer_ask_aed=valuation_data["dealer_ask_aed"],
        confidence_score=valuation_data["confidence_score"],
        comps=comp_models,
        is_live_listing=is_live_listing,
        estimated_value=valuation_data["fair_market_value_aed"],
        comparable_count=len(comp_models)
    )

@app.get("/valuate", response_model=PlateResponse)
def valuate_plate_get(
    plate: str = Query(..., description="Plate number, e.g. 333 or 77777"),
    code: str = Query(..., description="Plate code, e.g. A, AA, or CAT 1"),
    emirate: str = Query("dubai", description="Emirate name (dubai, abu dhabi, etc.)"),
    check_live: bool = Query(False, description="Check live active auction inventory if missing from DB")
):
    """
    GET valuation endpoint providing complete backwards compatibility
    with mobile and web query parameters.
    """
    req = PlateRequest(emirate=emirate, code=code, number=plate, check_live=check_live)
    return evaluate_plate(req)
