"""
Database abstraction layer for UAE Plate Valuator.
Supports Supabase (primary cloud DB) with automatic fallback to local SQLite (auctions.db).
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

DB_FILE = os.path.join(os.path.dirname(__file__), "auctions.db")

SEED_COMPS = [
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

def init_sqlite():
    """Ensure SQLite DB exists with auction_comps table and curated seed comps."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auction_comps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emirate TEXT NOT NULL,
            digit_count INTEGER NOT NULL,
            plate TEXT NOT NULL,
            price_aed INTEGER NOT NULL,
            date TEXT NOT NULL,
            source TEXT NOT NULL,
            UNIQUE(plate, price_aed, date)
        )
    """)
    # Insert seed comps using INSERT OR IGNORE
    cursor.executemany("""
        INSERT OR IGNORE INTO auction_comps (emirate, digit_count, plate, price_aed, date, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, SEED_COMPS)
    conn.commit()
    conn.close()

# Initialize local sqlite immediately
init_sqlite()

class DatabaseRepository:
    def __init__(self):
        self.client = None
        self._supabase_disabled = False
        self._init_supabase()

    def _init_supabase(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key and "supabase.co" in url and not url.startswith("https://your-project"):
            try:
                from supabase import create_client
                self.client = create_client(url, key)
            except Exception as e:
                print(f"Warning: Failed to initialize Supabase client: {e}")
                self.client = None

    def get_mode(self) -> str:
        return "supabase" if (self.client is not None and not self._supabase_disabled) else "sqlite_fallback"

    def get_comps(self, emirate: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch auction comps from Supabase or fallback to SQLite."""
        if self.client is not None and not self._supabase_disabled:
            try:
                query = self.client.table("auction_comps").select("*")
                if emirate:
                    query = query.eq("emirate", emirate.lower())
                response = query.order("id", desc=True).limit(limit).execute()
                if response.data:
                    return response.data
            except Exception as e:
                # Mark as disabled so subsequent calls in the same lifecycle don't stall on DNS/timeout
                print(f"Supabase query failed ({e}), falling back to SQLite.")
                self._supabase_disabled = True

        # Fallback to SQLite
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        if emirate:
            cursor.execute("""
                SELECT id, emirate, digit_count, plate, price_aed, date, source
                FROM auction_comps
                WHERE lower(emirate) = ?
                ORDER BY id DESC
                LIMIT ?
            """, (emirate.lower(), limit))
        else:
            cursor.execute("""
                SELECT id, emirate, digit_count, plate, price_aed, date, source
                FROM auction_comps
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": r[0],
                "emirate": r[1],
                "digit_count": r[2],
                "plate": r[3],
                "price_aed": r[4],
                "date": r[5],
                "source": r[6],
            }
            for r in rows
        ]

    def fetch_exact_match(self, plate_display: str) -> Optional[int]:
        """Check for exact historical auction comp for this plate."""
        if self.client is not None and not self._supabase_disabled:
            try:
                response = self.client.table("auction_comps").select("price_aed").eq("plate", plate_display.upper()).limit(1).execute()
                if response.data:
                    return response.data[0].get("price_aed")
            except Exception:
                pass

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT price_aed FROM auction_comps WHERE upper(plate) = ?", (plate_display.upper(),))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def fetch_nearest_comps(
        self,
        emirate: str,
        digit_count: int,
        target_price: int,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Fetch nearest price comps for comparable digit length in the same or nearby emirate."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT plate, price_aed, date, source
            FROM auction_comps
            WHERE lower(emirate) = ? AND digit_count = ?
            ORDER BY ABS(price_aed - ?) ASC
            LIMIT ?
        """, (emirate.lower(), digit_count, target_price, limit))
        rows = cursor.fetchall()

        if not rows:
            cursor.execute("""
                SELECT plate, price_aed, date, source
                FROM auction_comps
                WHERE digit_count = ?
                ORDER BY ABS(price_aed - ?) ASC
                LIMIT ?
            """, (digit_count, target_price, limit))
            rows = cursor.fetchall()

        if not rows:
            cursor.execute("""
                SELECT plate, price_aed, date, source
                FROM auction_comps
                ORDER BY ABS(price_aed - ?) ASC
                LIMIT ?
            """, (target_price, limit))
            rows = cursor.fetchall()

        conn.close()
        return [
            {"plate": r[0], "price_aed": r[1], "date": r[2], "source": r[3]}
            for r in rows
        ]

    def insert_comps(self, comps: List[Dict[str, Any]]) -> int:
        """Insert scraped or imported comps into both Supabase and SQLite."""
        if not comps:
            return 0
        
        # Always persist to SQLite locally
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        inserted_local = 0
        for c in comps:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO auction_comps (emirate, digit_count, plate, price_aed, date, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (c["emirate"], c["digit_count"], c["plate"], c["price_aed"], c["date"], c["source"]))
                if cursor.rowcount > 0:
                    inserted_local += 1
            except Exception:
                continue
        conn.commit()
        conn.close()

        # If Supabase is available, insert into cloud
        if self.client is not None and not self._supabase_disabled:
            try:
                self.client.table("auction_comps").upsert(comps).execute()
            except Exception as e:
                print(f"Supabase upsert warning: {e}")

        return inserted_local

# Global singleton repository
db = DatabaseRepository()
