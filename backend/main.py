import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from valuation import valuate
from database import db
from live_lookup import search_live_auction, probe_live_auction_inventory
from sources.aggregator import multi_source_aggregator

app = FastAPI(
    title="UAE Plate Valuation Engine",
    description="Multi-source market intelligence engine cross-referencing Dubai RTA, Emirates Auction, Dubizzle, and verified dealerships.",
    version="2.3.0"
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
    matched_source: Optional[str] = None
    is_live_listing: bool = False
    # Backward compatibility fields
    estimated_value: int
    comparable_count: int

@app.get("/health")
def health_check():
    """Health check endpoint reporting SQLite database metrics and total comps."""
    return {
        "status": "healthy",
        "database": "sqlite",
        "comps_in_db": db.count_comps()
    }

@app.get("/sources")
@app.get("/v1/sources")
def list_sources():
    """List all connected market data sources and database records breakdown."""
    return {
        "active_providers": multi_source_aggregator.list_sources(),
        "database_breakdown": db.count_by_source(),
        "total_comps": db.count_comps()
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
    emirate: Optional[str] = Query(None, description="Optional filter by emirate (e.g. dubai, abu dhabi, sharjah)"),
    source: Optional[str] = Query(None, description="Optional filter by source (e.g. RTA, Emirates Auction, Dubizzle)"),
    limit: int = Query(50, ge=1, le=100)
):
    """Retrieve historical and live auction comparable records across all sources."""
    try:
        data = db.get_comps(emirate=emirate, source=source, limit=limit)
        return {"data": data, "count": len(data), "database": "sqlite"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve auction comps.")

@app.post("/v1/evaluate", response_model=PlateResponse)
def evaluate_plate(payload: PlateRequest):
    """
    Comprehensive multi-source valuation endpoint.
    1. Cross-references SQLite database for exact comp across RTA, Emirates Auction & Dealerships.
    2. Checks live auction platforms (Emirates Auction) if live probe requested.
    3. Runs heuristic valuation engine and retrieves nearest benchmark comps.
    """
    num = payload.number.strip()
    raw_code = payload.code.strip()
    emirate = payload.emirate.strip()

    if not num.isdigit() or not (1 <= len(num) <= 5):
        raise HTTPException(status_code=400, detail="Plate number must be between 1 and 5 numeric digits.")

    if not raw_code:
        raise HTTPException(status_code=400, detail="Plate code or category is required.")

    temp_display = f"{emirate.upper()} {raw_code.upper()} {num}"
    exact_price = None
    matched_source = None
    is_live_listing = False

    # 1. Check local multi-source database for exact match
    exact_comp = db.fetch_exact_match(temp_display)
    if exact_comp:
        exact_price = exact_comp["price_aed"]
        matched_source = exact_comp["source"]
    else:
        # Check providers directly
        multi_match = multi_source_aggregator.search_all_sources(emirate, raw_code, num)
        if multi_match:
            exact_price = multi_match["price_aed"]
            matched_source = multi_match["source"]

    # 2. If not found in static records and live crawl requested, probe live auction inventory
    if not exact_price and payload.check_live:
        live_result = search_live_auction(
            emirate=emirate,
            code=raw_code,
            number=num,
            allow_live_crawl=True
        )
        if live_result:
            exact_price = live_result.get("price_aed")
            matched_source = live_result.get("source", "Emirates Auction Live Active")
            is_live_listing = True

    # 3. Run heuristic valuation engine
    valuation_data = valuate(
        emirate=emirate,
        code=raw_code,
        number=num,
        exact_comp_price=exact_price
    )

    display_patterns = list(valuation_data["patterns"])
    if matched_source:
        display_patterns.insert(0, f"Source Verified: {matched_source}")
    elif is_live_listing:
        display_patterns.insert(0, "Emirates Auction Live Active Listing")

    # 4. Fetch nearest price comps from multi-source database
    nearest_comps = db.fetch_nearest_comps(
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
        for c in nearest_comps
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
        matched_source=matched_source,
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
