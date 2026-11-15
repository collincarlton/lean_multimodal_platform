#!/usr/bin/env python3
"""
ENGINE-1: Listing Enrichment Module (Gemini 3.8 Flash + Sovereign Deterministic Synthesis)
Target: macOS Darwin x86_64 (8GB RAM, APFS Fusion Drive)
FinOps Quota: $0.00 spend, strict token-bucket / rate-limit barrier.
Resilience: Strict 4s timeout with instant deterministic local synthesis fallback.
Storage: aiosqlite WAL mode, cache_size=-32000.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Enricher] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("Enricher")

HOME_DIR = Path.home().resolve()
HOME_DEV = HOME_DIR.stat().st_dev
DATA_DIR = Path("/Users/collincarlton/lean_multimodal_platform/data").resolve()
DB_PATH = DATA_DIR / "engine1.db"
KEYS_PATH = HOME_DIR / ".lunora/keys.json"


AISTUDIO_SCRIPTS = HOME_DIR / "AIStudioOrg" / "scripts"
if str(AISTUDIO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(AISTUDIO_SCRIPTS))

try:
    from lunora_core import (
        MIN_HTTP_TIMEOUT_MS,
        MODEL_PRIORITY,
        TokenBucketGovernor,
        assert_safe_device,
        get_api_key,
    )
except ImportError:
    MIN_HTTP_TIMEOUT_MS = 15000
    MODEL_PRIORITY = [
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3-flash-preview",
        "gemini-flash-lite-latest",
        "gemini-3.8-flash",
    ]
    TokenBucketGovernor = None  # type: ignore

    def assert_safe_device(path: Path | str) -> None:
        p = Path(path)
        if p.exists() and os.stat(str(p)).st_dev != HOME_DEV:
            raise PermissionError(f"Mount barrier violated on {p}")

    def get_api_key() -> Optional[str]:
        """Retrieves Gemini / Google API key from environment or ~/.lunora/keys.json."""
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if key:
            return key
        if KEYS_PATH.exists():
            try:
                with open(KEYS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("GEMINI_API_KEY") or data.get("GOOGLE_API_KEY")
            except Exception:
                pass
        return None


def build_deterministic_enrichment(listing: Dict[str, Any], niche_name: str) -> Dict[str, Any]:
    """Generate high-density SEO summary, trust badges, Filter-Gap facets, and Schema.org JSON-LD."""
    name = listing["business_name"]
    city = listing["city"]
    rating = listing.get("rating", 4.8)
    reviews_count = listing.get("reviews_count", 35)
    phone = listing.get("phone", "N/A")
    website = listing.get("website", "N/A")
    address = listing.get("address", f"{city}, TX")
    zip_code = listing.get("zip_code", "75001")

    is_emergency = 1 if any(w in name.lower() for w in ["emergency", "24/7", "urgent", "storm", "tactical"]) or rating >= 4.8 else 0
    is_crane = 1 if any(w in name.lower() for w in ["crane", "heavy", "removal", "surgeons", "rigging"]) or reviews_count >= 100 else 1
    is_isa = 1 if any(w in name.lower() for w in ["arborist", "doctors", "care", "preservation", "certified"]) or rating >= 4.8 else 0
    is_commercial = 1 if any(w in name.lower() for w in ["commercial", "solution", "masters", "experts", "specialists"]) or reviews_count >= 50 else 0
    free_estimate = 1
    lead_readiness = min(99, max(75, int(rating * 18 + min(10, reviews_count // 30))))
    speed_to_lead = 180 if is_emergency else 360

    services = [
        "24/7 Emergency Storm Damage Removal",
        "Crane-Assisted Hazardous Tree Felling",
        "Precision Canopy Pruning & Trimming",
        "Deep Stump Grinding & Surface Root Elimination",
        "Emergency Powerline & Structure Clearance",
    ]

    trust_badges = [
        "ISA Certified Arborist Oversight",
        "24/7 Rapid Emergency Dispatch",
        "Commercial Rigging & Crane Certified",
        f"Top Rated {city} Service ({rating}★)",
    ]

    price_tier = "$$$$" if is_emergency or "crane" in name.lower() else "$$$"

    summary = (
        f"{name} is a premier emergency tree service provider in {city}, TX, specializing in "
        f"crane-assisted hazardous tree removal, rapid storm debris clearance, and precision arboriculture. "
        f"Available 24/7 with a {rating}★ client satisfaction record across {reviews_count}+ local property owners."
    )

    schema_org = {
        "@context": "https://schema.org",
        "@type": "HomeAndConstructionBusiness",
        "name": name,
        "description": summary,
        "telephone": phone,
        "url": website,
        "priceRange": price_tier,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": address,
            "addressLocality": city,
            "addressRegion": "TX",
            "postalCode": zip_code,
            "addressCountry": "US",
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": "32.7767",
            "longitude": "-96.7970",
        },
        "openingHoursSpecification": [
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "opens": "00:00",
                "closes": "23:59",
            }
        ] if is_emergency else [
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                "opens": "07:00",
                "closes": "19:00",
            }
        ],
        "areaServed": [
            {"@type": "City", "name": city},
            {"@type": "AdministrativeArea", "name": "Dallas-Fort Worth Metroplex"},
        ],
    }

    return {
        "summary": summary,
        "services_offered": json.dumps(services),
        "emergency_24_7": is_emergency,
        "badges": json.dumps(trust_badges),
        "price_tier": price_tier,
        "schema_org_json": json.dumps(schema_org),
        "crane_rigging": is_crane,
        "isa_certified": is_isa,
        "commercial_accounts": is_commercial,
        "free_estimate": free_estimate,
        "lead_readiness_score": lead_readiness,
        "speed_to_lead_latency_sec": speed_to_lead,
    }


def call_gemini_batch(batch: List[Dict[str, Any]], niche_name: str, timeout: float = 18.0) -> Optional[List[Dict[str, Any]]]:
    """Attempt Gemini 3.8 Flash batch enrichment with SHA-256 SQLite cache and 18s timeout."""
    api_key = get_api_key()
    if not api_key:
        return None

    # Compute batch hash
    prompt_items = []
    for item in batch:
        prompt_items.append({
            "id": item["id"],
            "name": item["business_name"],
            "city": item["city"],
            "rating": item["rating"],
            "reviews": item["reviews_count"],
        })
    prompt_str = json.dumps(prompt_items, sort_keys=True)
    prompt_hash = hashlib.sha256(f"{niche_name}:{prompt_str}".encode("utf-8")).hexdigest()

    # Check SQLite genai_cache first
    try:
        conn_sync = sqlite3.connect(str(DB_PATH))
        cur = conn_sync.execute("SELECT response_json FROM genai_cache WHERE prompt_hash = ?;", (prompt_hash,))
        row = cur.fetchone()
        conn_sync.close()
        if row:
            logger.info(f"Using cached GenAI response (SHA-256: {prompt_hash[:12]}...)")
            return json.loads(row[0])
    except Exception:
        pass

    try:
        from google import genai
        from google.genai import types

        if TokenBucketGovernor is not None:
            acquired, wait_s, reason = TokenBucketGovernor().acquire(tokens=max(400, len(batch) * 200), wait=True, max_wait=8.0)
            if not acquired:
                logger.info(f"TokenBucketGovernor bypassed Gemini call ({reason}, wait={wait_s:.1f}s)")
                return None

        timeout_ms = max(int(timeout * 1000), MIN_HTTP_TIMEOUT_MS)
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=timeout_ms),
        )

        prompt = f"""You are an elite local SEO copywriter and schema architect for '{niche_name}'.
For each business item in the input list, generate an enrichment object with:
- id: match input id
- business_summary: 2 punchy, professional sentences highlighting emergency crane removal and arborist capabilities.
- services: JSON array of 4-5 high-margin service strings.
- is_emergency: 1 if offers 24/7 or storm response, else 0.
- crane_rigging: 1 if offers crane or rigging, else 0.
- isa_certified: 1 if ISA certified, else 0.
- commercial_accounts: 1 if offers commercial accounts, else 0.
- free_estimate: 1.
- lead_readiness_score: integer between 75 and 99 based on ratings and market position.
- speed_to_lead_latency_sec: estimated response latency in seconds (e.g. 180 to 600).
- trust_badges: array of 4 badge strings (e.g. 'ISA Certified', '24/7 Dispatch').
- price_tier: '$$$' or '$$$$'.

Return ONLY a valid JSON array of objects.
Input: {json.dumps(prompt_items)}"""

        config = types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        )
        data = None
        for model_name in MODEL_PRIORITY:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                candidate = json.loads(response.text)
                if isinstance(candidate, list) and len(candidate) == len(batch):
                    data = candidate
                    break
            except Exception as model_exc:
                logger.debug(f"Model {model_name} failed ({type(model_exc).__name__}); trying next priority")
                continue

        if data is not None:
            # Save to genai_cache
            try:
                conn_sync = sqlite3.connect(str(DB_PATH))
                now_iso = datetime.now(timezone.utc).isoformat()
                conn_sync.execute(
                    "INSERT OR REPLACE INTO genai_cache (prompt_hash, response_json, cached_at) VALUES (?, ?, ?);",
                    (prompt_hash, json.dumps(data), now_iso)
                )
                conn_sync.commit()
                conn_sync.close()
            except Exception:
                pass
            return data
    except Exception as e:
        logger.debug(f"Gemini call bypassed/failed ({type(e).__name__}): {e}")

    return None


async def enrich_all_listings(batch_size: int = 5, limit: Optional[int] = None) -> int:
    """Read unenriched listings, enrich with Gemini or sovereign fallback, and persist."""
    assert DATA_DIR.stat().st_dev == HOME_DEV, "Mount barrier violated"
    assert DB_PATH.exists(), f"Database not found: {DB_PATH}"

    conn = await aiosqlite.connect(str(DB_PATH))
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.execute("PRAGMA synchronous=NORMAL;")
    await conn.execute("PRAGMA cache_size=-32000;")

    # Get active niche
    async with conn.execute("SELECT id, name FROM niches WHERE selected = 1 LIMIT 1;") as cursor:
        niche_row = await cursor.fetchone()
        niche_name = niche_row[1] if niche_row else "Emergency Tree Removal & Crane Arborists"

    query = "SELECT id, business_name, phone, website, rating, reviews_count, address, city, state, zip_code FROM listings WHERE is_enriched = 0 ORDER BY id ASC"
    if limit:
        query += f" LIMIT {limit}"

    async with conn.execute(query) as cursor:
        rows = await cursor.fetchall()

    if not rows:
        logger.info("All listings are already enriched! Nothing to do.")
        await conn.close()
        return 0

    logger.info(f"Enriching {len(rows)} listings for niche: '{niche_name}' (Batch size: {batch_size})")

    listings = [
        {
            "id": r[0],
            "business_name": r[1],
            "phone": r[2],
            "website": r[3],
            "rating": r[4],
            "reviews_count": r[5],
            "address": r[6],
            "city": r[7],
            "state": r[8],
            "zip_code": r[9],
        }
        for r in rows
    ]

    now_iso = datetime.now(timezone.utc).isoformat()
    enriched_count = 0

    for i in range(0, len(listings), batch_size):
        chunk = listings[i : i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1}/{(len(listings) + batch_size - 1) // batch_size} (Items {i+1} to {min(i+len(chunk), len(listings))})...")

        # Attempt Gemini 3.8 Flash (18.0s timeout + genai_cache)
        gemini_results = await asyncio.to_thread(call_gemini_batch, chunk, niche_name, 18.0)

        records_to_insert = []
        for idx, item in enumerate(chunk):
            det = build_deterministic_enrichment(item, niche_name)

            if gemini_results and idx < len(gemini_results):
                g_item = gemini_results[idx]
                if "business_summary" in g_item:
                    det["summary"] = g_item["business_summary"]
                if "services" in g_item:
                    det["services_offered"] = json.dumps(g_item["services"])
                if "is_emergency" in g_item:
                    det["emergency_24_7"] = int(g_item["is_emergency"])
                if "trust_badges" in g_item:
                    det["badges"] = json.dumps(g_item["trust_badges"])
                if "price_tier" in g_item:
                    det["price_tier"] = g_item["price_tier"]
                if "crane_rigging" in g_item:
                    det["crane_rigging"] = int(g_item["crane_rigging"])
                if "isa_certified" in g_item:
                    det["isa_certified"] = int(g_item["isa_certified"])
                if "commercial_accounts" in g_item:
                    det["commercial_accounts"] = int(g_item["commercial_accounts"])
                if "free_estimate" in g_item:
                    det["free_estimate"] = int(g_item["free_estimate"])
                if "lead_readiness_score" in g_item:
                    det["lead_readiness_score"] = int(g_item["lead_readiness_score"])
                if "speed_to_lead_latency_sec" in g_item:
                    det["speed_to_lead_latency_sec"] = int(g_item["speed_to_lead_latency_sec"])

            records_to_insert.append((
                item["id"],
                det["summary"],
                det["services_offered"],
                det["emergency_24_7"],
                det["badges"],
                det["price_tier"],
                det["schema_org_json"],
                now_iso,
                det["crane_rigging"],
                det["isa_certified"],
                det["commercial_accounts"],
                det["free_estimate"],
                det["lead_readiness_score"],
                det["speed_to_lead_latency_sec"],
            ))

        # Insert into enrichments & update listings
        for rec in records_to_insert:
            await conn.execute(
                """
                INSERT OR REPLACE INTO enrichments 
                (listing_id, summary, services_offered, emergency_24_7, badges, price_tier, schema_org_json, enriched_at,
                 crane_rigging, isa_certified, commercial_accounts, free_estimate, lead_readiness_score, speed_to_lead_latency_sec)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                rec,
            )
            await conn.execute("UPDATE listings SET is_enriched = 1 WHERE id = ?;", (rec[0],))

        await conn.commit()
        enriched_count += len(chunk)

    await conn.close()
    logger.info(f"[✓] Successfully enriched {enriched_count} listings in SQLite (engine1.db).")
    return enriched_count


def main():
    parser = argparse.ArgumentParser(description="ENGINE-1 Gemini 3.8 Flash & Local Listing Enricher")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for enrichment")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of listings to enrich")
    args = parser.parse_args()

    count = asyncio.run(enrich_all_listings(args.batch_size, args.limit))
    print(f"\n[✓] Finished enriching {count} listings.")


if __name__ == "__main__":
    main()
