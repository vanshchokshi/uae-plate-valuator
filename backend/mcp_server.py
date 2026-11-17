"""
FastMCP Server for UAE Plate Valuator
Exposes tools for AI agents to evaluate plates and fetch historical market comps.
"""

from mcp.server.fastmcp import FastMCP
from database import db
from valuation import valuate

mcp = FastMCP("PlateValuator")

@mcp.tool()
def fetch_market_comps(emirate: str = "dubai", limit: int = 20) -> str:
    """Fetch live license plate auction comps from the comps database."""
    comps = db.get_comps(emirate=emirate, limit=limit)
    return str(comps)

@mcp.tool()
def evaluate_plate(emirate: str, code: str, number: str) -> str:
    """
    Calculate fair market value, liquidation value, dealer ask, and identify
    plate patterns for a UAE vehicle license plate.
    """
    exact = db.fetch_exact_match(f"{emirate.upper()} {code.upper()} {number}")
    result = valuate(emirate=emirate, code=code, number=number, exact_comp_price=exact)
    nearest = db.fetch_nearest_comps(
        emirate=result["emirate"],
        digit_count=result["digit_count"],
        target_price=result["fair_market_value_aed"],
        limit=3
    )
    result["nearest_comps"] = nearest
    return str(result)

if __name__ == "__main__":
    mcp.run()
