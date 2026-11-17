"""
Utility script to quickly inspect market comps from SQLite database.
"""

from database import db

if __name__ == "__main__":
    comps = db.get_comps(emirate="dubai", limit=10)
    print(f"Loaded {len(comps)} Dubai comps (Total records in SQLite: {db.count_comps()}):")
    for c in comps:
        print(f"  {c['plate']} -> AED {c['price_aed']:,} ({c['date']}, {c['source']})")
