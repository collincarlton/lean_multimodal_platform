#!/usr/bin/env python3
"""
ENGINE-1: Niche Evaluator & Schema Initializer
Target: macOS Darwin x86_64 (8GB RAM, APFS Fusion Drive)
Storage Invariant: SQLite WAL, synchronous=NORMAL, cache_size=-32000 (32MB ceiling)
Zero-Capital Law: $0.00 spend.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import aiosqlite

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [NicheEvaluator] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("NicheEvaluator")

HOME_DIR = Path.home().resolve()
HOME_DEV = HOME_DIR.stat().st_dev
ENGINE_DIR = Path("/Users/collincarlton/lean_multimodal_platform/engine1").resolve()
DATA_DIR = Path("/Users/collincarlton/lean_multimodal_platform/data").resolve()
DB_PATH = DATA_DIR / "engine1.db"


def assert_safe_device(path: Path) -> None:
    if not path.exists():
        return
    if path.stat().st_dev != HOME_DEV:
        raise PermissionError(f"Virtual mount boundary violation on {path}")


async def get_db_connection() -> aiosqlite.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    assert_safe_device(DATA_DIR)

    conn = await aiosqlite.connect(str(DB_PATH), timeout=15.0)
    await conn.execute("PRAGMA journal_mode = WAL;")
    await conn.execute("PRAGMA cache_size = -32000;")
    await conn.execute("PRAGMA synchronous = NORMAL;")
    await conn.execute("PRAGMA temp_store = MEMORY;")
    return conn


async def init_schema(conn: aiosqlite.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS niches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            aov_estimate REAL NOT NULL,
            urgency_level TEXT NOT NULL,
            competition_score REAL NOT NULL,
            lead_value_est REAL NOT NULL,
            overall_score REAL NOT NULL,
            selected INTEGER DEFAULT 0,
            target_queries TEXT NOT NULL,
            evaluated_at TEXT NOT NULL
        );
        """
    )
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche_id INTEGER NOT NULL REFERENCES niches(id),
            business_name TEXT NOT NULL,
            phone TEXT,
            website TEXT,
            rating REAL,
            reviews_count INTEGER DEFAULT 0,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            is_verified INTEGER DEFAULT 0,
            is_enriched INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            UNIQUE(niche_id, business_name, phone)
        );
        """
    )
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS enrichments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER UNIQUE NOT NULL REFERENCES listings(id),
            summary TEXT,
            services_offered TEXT,
            emergency_24_7 INTEGER DEFAULT 0,
            badges TEXT,
            price_tier TEXT,
            schema_org_json TEXT,
            enriched_at TEXT NOT NULL
        );
        """
    )
    await conn.commit()
    logger.info("Initialized Engine-1 SQLite schema with WAL + 32MB cache.")


NICHES_CANDIDATES: List[Dict[str, Any]] = [
    {
        "name": "Emergency Tree Removal & Crane Arborists",
        "category": "Arboriculture & Tree Care",
        "aov_estimate": 2850.0,
        "urgency_level": "CRITICAL",
        "competition_score": 34.0,  # Lower is less crowded
        "lead_value_est": 175.0,
        "overall_score": 93.5,
        "target_queries": [
            "emergency tree removal Dallas TX",
            "crane tree service Fort Worth TX",
            "storm damage tree removal Arlington TX",
            "emergency tree service Plano TX",
            "24 hour tree removal Frisco TX",
            "hazardous tree cutting Irving TX",
            "commercial tree arborist Denton TX",
            "stump grinding tree removal Garland TX",
        ],
    },
    {
        "name": "Commercial & Residential Epoxy Flooring",
        "category": "Flooring & Concrete Coatings",
        "aov_estimate": 4200.0,
        "urgency_level": "MODERATE",
        "competition_score": 52.0,
        "lead_value_est": 125.0,
        "overall_score": 85.0,
        "target_queries": [
            "garage epoxy flooring Dallas TX",
            "commercial concrete coating Fort Worth TX",
            "metallic epoxy floor installers Plano TX",
            "polyaspartic garage floor Frisco TX",
        ],
    },
    {
        "name": "Foundation Repair & Pier Underpinning",
        "category": "Structural Engineering & Foundation",
        "aov_estimate": 7500.0,
        "urgency_level": "HIGH",
        "competition_score": 68.0,
        "lead_value_est": 220.0,
        "overall_score": 88.0,
        "target_queries": [
            "foundation repair Dallas TX",
            "pier and beam foundation Fort Worth TX",
            "house leveling foundation repair Arlington TX",
            "slab foundation repair Plano TX",
        ],
    },
]


async def evaluate_and_seed_niches() -> Dict[str, Any]:
    conn = await get_db_connection()
    try:
        await init_schema(conn)

        # Find best niche by overall_score
        best_score = max(n["overall_score"] for n in NICHES_CANDIDATES)

        for n in NICHES_CANDIDATES:
            is_selected = 1 if n["overall_score"] == best_score else 0
            await conn.execute(
                """
                INSERT INTO niches (
                    name, category, aov_estimate, urgency_level, competition_score,
                    lead_value_est, overall_score, selected, target_queries, evaluated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    aov_estimate=excluded.aov_estimate,
                    overall_score=excluded.overall_score,
                    selected=excluded.selected,
                    target_queries=excluded.target_queries,
                    evaluated_at=excluded.evaluated_at;
                """,
                (
                    n["name"],
                    n["category"],
                    n["aov_estimate"],
                    n["urgency_level"],
                    n["competition_score"],
                    n["lead_value_est"],
                    n["overall_score"],
                    is_selected,
                    json.dumps(n["target_queries"]),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        await conn.commit()

        # Fetch selected niche
        async with conn.execute("SELECT id, name, category, overall_score, target_queries FROM niches WHERE selected = 1;") as cursor:
            row = await cursor.fetchone()
            if not row:
                raise ValueError("No winning niche selected!")

            selected_niche = {
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "overall_score": row[3],
                "target_queries": json.loads(row[4]),
            }

        logger.info(f"Winning Niche Selected: '{selected_niche['name']}' (Score: {selected_niche['overall_score']})")
        return selected_niche
    finally:
        await conn.close()


async def get_selected_niche() -> Dict[str, Any]:
    conn = await get_db_connection()
    try:
        async with conn.execute("SELECT id, name, category, overall_score, target_queries FROM niches WHERE selected = 1;") as cursor:
            row = await cursor.fetchone()
            if not row:
                return await evaluate_and_seed_niches()
            return {
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "overall_score": row[3],
                "target_queries": json.loads(row[4]),
            }
    finally:
        await conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Engine-1 Niche Evaluator")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate niches and seed database")
    parser.add_argument("--test", action="store_true", help="Run self-test")
    args = parser.parse_args()

    niche = asyncio.run(evaluate_and_seed_niches())
    print("\n" + "=" * 60)
    print("🎯 ENGINE-1 WINNING NICHE SELECTION")
    print("=" * 60)
    print(f"  Name           : {niche['name']}")
    print(f"  Category       : {niche['category']}")
    print(f"  Overall Score  : {niche['overall_score']}/100")
    print(f"  Target Queries : {len(niche['target_queries'])} query targets")
    print(f"  Database Path  : {DB_PATH}")
    print("=" * 60 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
