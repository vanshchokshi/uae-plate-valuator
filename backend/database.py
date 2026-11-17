"""
SQLite Database Layer for UAE Plate Valuator.
Fast, zero-config, embedded database for historical and live auction comps.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
from sources.aggregator import multi_source_aggregator

DB_FILE = os.path.join(os.path.dirname(__file__), "auctions.db")

def init_sqlite():
    """Ensure SQLite DB exists with schema, indexes, and multi-source benchmarks."""
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
    # Performance indexes for sub-millisecond queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comps_emirate_digits ON auction_comps(emirate, digit_count, price_aed)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comps_plate ON auction_comps(plate)")

    # Seed multi-source benchmark comps from RTA, Emirates Auction, Dubizzle, and Luxury Dealerships
    benchmarks = multi_source_aggregator.get_all_benchmark_comps(limit=100)
    cursor.executemany("""
        INSERT OR IGNORE INTO auction_comps (emirate, digit_count, plate, price_aed, date, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [(b["emirate"], b["digit_count"], b["plate"], b["price_aed"], b["date"], b["source"]) for b in benchmarks])

    conn.commit()
    conn.close()

# Initialize immediately
init_sqlite()

class DatabaseRepository:
    def __init__(self):
        self.db_file = DB_FILE

    def count_comps(self) -> int:
        """Return total count of comparable plates stored."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM auction_comps")
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def count_by_source(self) -> List[Dict[str, Any]]:
        """Return breakdown of records by source."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT source, COUNT(*) FROM auction_comps GROUP BY source ORDER BY COUNT(*) DESC")
        rows = cursor.fetchall()
        conn.close()
        return [{"source": r[0], "count": r[1]} for r in rows]

    def get_comps(self, emirate: Optional[str] = None, source: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch auction comps from SQLite with optional emirate and source filters."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        query = "SELECT id, emirate, digit_count, plate, price_aed, date, source FROM auction_comps WHERE 1=1"
        params: List[Any] = []
        
        if emirate:
            query += " AND lower(emirate) = ?"
            params.append(emirate.lower())
        if source:
            query += " AND lower(source) LIKE ?"
            params.append(f"%{source.lower()}%")
            
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, tuple(params))
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

    def fetch_exact_match(self, plate_display: str) -> Optional[Dict[str, Any]]:
        """Check for exact comp across database for this plate."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT price_aed, date, source FROM auction_comps WHERE upper(plate) = ?", (plate_display.upper(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"price_aed": row[0], "date": row[1], "source": row[2]}
        return None

    def fetch_nearest_comps(
        self,
        emirate: str,
        digit_count: int,
        target_price: int,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Fetch nearest price comps for comparable digit length in the same or nearby emirate."""
        conn = sqlite3.connect(self.db_file)
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
        """Insert scraped or imported comps into SQLite."""
        if not comps:
            return 0
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        inserted = 0
        for c in comps:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO auction_comps (emirate, digit_count, plate, price_aed, date, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (c["emirate"], c["digit_count"], c["plate"], c["price_aed"], c["date"], c["source"]))
                if cursor.rowcount > 0:
                    inserted += 1
            except Exception:
                continue
        conn.commit()
        conn.close()
        return inserted

# Global singleton repository
db = DatabaseRepository()
