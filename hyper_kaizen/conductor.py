#!/usr/bin/env python3
"""
Hyper-Kaizen Master 7-Loop Conductor CLI.
Usage:
  python3 -m lean_multimodal_platform.hyper_kaizen.conductor --niche-slug emergency-tree-dfw --target-count 100 --with-kaizen-dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .core_guard import HOME_DIR, HOME_DEV, assert_safe_device, init_hyper_kaizen_schema
from .deep_refinery import refine_niche_listings
from .demand_scout import get_niche_spec, score_niches
from .kaizen_mutator import run_kaizen_evolution
from .monetizer_and_links import run_monetizer_and_links
from .pseo_compiler import compile_directory_site
from .telemetry_harvester import inspect_and_ping_dist

STATE_SNAPSHOT_PATH = HOME_DIR / ".lunora" / "state" / "hyper_kaizen_last_run.json"


def run_hyper_kaizen_pipeline(
    *,
    niche_slug: str = "emergency-tree-dfw",
    target_count: int = 100,
    crawl_limit: int = 12,
    with_kaizen_dry_run: bool = True,
    apply_mutations: bool = False,
    simulate_gsc: bool = False,
    live_network: bool = False,
    live_gsc: bool = False,
    use_genai: bool = True,
) -> Dict[str, Any]:
    """Execute Loops 1 through 7 in sequence and persist snapshot to ~/.lunora/state/."""
    assert HOME_DIR.stat().st_dev == HOME_DEV, "APFS HOME_DEV invariant mismatch"
    init_hyper_kaizen_schema()

    # Loop 1: Niche Demand & Filter-Gap Scout
    niche_scores = score_niches()
    spec = get_niche_spec(niche_slug)

    # Loop 2: Deep Refinery & Website Inspection Crossover
    refined = refine_niche_listings(
        spec,
        target_count=target_count,
        crawl_limit=crawl_limit,
        use_genai=use_genai,
    )
    listings = refined["listings"]

    # Loop 3 & 4: Info-Gain Gate + Static pSEO Compiler
    compiled = compile_directory_site(spec, listings, mirror_to_docs=(niche_slug == "emergency-tree-dfw"))

    # Loop 5: Telemetry & IndexNow Harvester
    telemetry = inspect_and_ping_dist(
        spec,
        compiled["sitemap_urls"],
        live_network=live_network,
        live_gsc=live_gsc,
        simulate_gsc=simulate_gsc,
    )

    # Loop 6: Kaizen Fitness & Striking-Distance Evolution
    kaizen_dry = False if apply_mutations else with_kaizen_dry_run
    evolution = run_kaizen_evolution(spec, listings, dry_run=kaizen_dry)

    # Loop 7: Monetizer, Backlinks & Engine 1 -> Engine 2 Crossover
    monetizer = run_monetizer_and_links(spec, listings)

    summary: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "niche_slug": niche_slug,
        "loop1_niches_ranked": len(niche_scores),
        "loop2_refined": {
            "count": refined["count"],
            "rejected_fake": refined["rejected_fake"],
            "crawled": refined["crawled"],
            "enriched_new": refined["enriched_new"],
            "audits_queued": refined["audits_queued"],
            "memory_mb": refined["memory"],
        },
        "loop3_4_compiled": {k: v for k, v in compiled.items() if k != "sitemap_urls"},
        "loop5_telemetry": telemetry,
        "loop6_evolution": evolution,
        "loop7_monetizer": monetizer,
    }

    STATE_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    assert_safe_device(STATE_SNAPSHOT_PATH.parent)
    STATE_SNAPSHOT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="LUNORA 7-Loop Hyper-Kaizen Directory Conductor")
    parser.add_argument("--niche-slug", default="emergency-tree-dfw")
    parser.add_argument("--target-count", type=int, default=100)
    parser.add_argument("--crawl-limit", type=int, default=12)
    parser.add_argument("--with-kaizen-dry-run", action="store_true")
    parser.add_argument("--apply-mutations", action="store_true")
    parser.add_argument("--simulate-gsc", action="store_true")
    parser.add_argument("--live-network", action="store_true")
    parser.add_argument("--live-gsc", action="store_true")
    parser.add_argument("--no-genai", action="store_true")
    args = parser.parse_args()

    try:
        result = run_hyper_kaizen_pipeline(
            niche_slug=args.niche_slug,
            target_count=args.target_count,
            crawl_limit=args.crawl_limit,
            with_kaizen_dry_run=args.with_kaizen_dry_run or (not args.apply_mutations),
            apply_mutations=args.apply_mutations,
            simulate_gsc=args.simulate_gsc,
            live_network=args.live_network,
            live_gsc=args.live_gsc,
            use_genai=not args.no_genai,
        )
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        err_msg = f"hyper_kaizen.conductor exception: {type(exc).__name__}: {exc}"
        try:
            scripts_dir = str(HOME_DIR / "AIStudioOrg" / "scripts")
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
            import sqlite3
            from lunora_execution_fault_analyzer import SYS_DB_PATH, analyze_failed_runs, get_sqlite_connection
            if SYS_DB_PATH.exists():
                with get_sqlite_connection(SYS_DB_PATH) as conn:
                    conn.execute(
                        "INSERT INTO runs (raw_intent, tier, plan_json, success, log) VALUES (?, ?, ?, 0, ?)",
                        (f"hyper_kaizen:{args.niche_slug}", "hyper_kaizen", "{}", err_msg[:1000]),
                    )
                    conn.commit()
            analyze_failed_runs()
        except Exception:
            pass
        print(json.dumps({"error": err_msg}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
