"""
Utility script to quickly inspect market comps from database.
"""

from database import db

if __name__ == "__main__":
    comps = db.get_comps(emirate="dubai", limit=10)
    print(f"Loaded {len(comps)} comps via {db.get_mode()} mode:")
    for c in comps:
        print(f"  {c['plate']} -> AED {c['price_aed']:,} ({c['date']}, {c['source']})")
