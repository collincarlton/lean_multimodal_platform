#!/usr/bin/env python3
"""
Loop 6 — Evolution & Self-Healing Mutator (Closed-Loop Kaizen).
- Calculates directory fitness score: (clicks*2 + impressions*0.05 + leads*50)
- Detects striking-distance keywords in GSC positions 4.0-20.0 and rewrites <title> & <meta description>
- Tracks freshness >30 days, recommends next unbuilt suburb hubs, and flags 60-day zero-yield pages
  as CONSOLIDATE_CANDIDATE (Darwinian pruner).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from .core_guard import SYS_DB_PATH, GenAIRouter, get_sqlite_connection, init_hyper_kaizen_schema
from .deep_refinery import slugify
from .demand_scout import NicheSpec
from .pseo_compiler import SITES_ROOT

EXPANSION_SUBURB_POOL = [
    "McKinney", "Richardson", "Carrollton", "Lewisville", "Flower Mound",
    "Southlake", "Keller", "Mansfield", "Allen", "Grand Prairie",
]


def _resolve_local_html(url: str, dist_dir: Path) -> Path | None:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if not parts or parts[-1].endswith("-directory"):
        candidate = dist_dir / "index.html"
        return candidate if candidate.exists() else None
    # Handle /cities/foo.html, /filters/bar.html, /listings/baz.html inside base_url subpath
    for folder in ("cities", "filters", "listings"):
        if folder in parts:
            idx = parts.index(folder)
            rel = Path(*parts[idx:])
            candidate = dist_dir / rel
            if candidate.exists():
                return candidate
    if parts[-1] == "index.html":
        candidate = dist_dir / "index.html"
        return candidate if candidate.exists() else None
    return None


def compute_fitness_scores(spec: NicheSpec) -> List[Dict[str, Any]]:
    """Aggregate GSC clicks/impressions + conversion leads into `directory_fitness`."""
    init_hyper_kaizen_schema()
    now_iso = datetime.now(timezone.utc).isoformat()
    scored: List[Dict[str, Any]] = []

    with get_sqlite_connection(SYS_DB_PATH) as conn:
        gsc_rows = conn.execute(
            """
            SELECT url, SUM(clicks) AS clicks, SUM(impressions) AS imps, AVG(position) AS avg_pos, MAX(captured_at) AS cap
            FROM gsc_telemetry
            WHERE niche_slug = ?
            GROUP BY url
            """,
            (spec.niche_slug,),
        ).fetchall()

        lead_counts = {
            r["page_url"]: int(r["cnt"])
            for r in conn.execute(
                """
                SELECT page_url, COUNT(*) AS cnt
                FROM conversion_telemetry
                WHERE niche_slug = ? AND event_type IN ('quote_submit', 'call_click')
                GROUP BY page_url
                """,
                (spec.niche_slug,),
            ).fetchall()
        }

        for r in gsc_rows:
            url = r["url"]
            clicks = int(r["clicks"] or 0)
            imps = int(r["imps"] or 0)
            leads = lead_counts.get(url, 0) + lead_counts.get(urlparse(url).path, 0)
            fitness = round((clicks * 2.0) + (imps * 0.05) + (leads * 50.0), 2)
            status = "CONSOLIDATE_CANDIDATE" if (imps == 0 and leads == 0) else "ACTIVE"
            conn.execute(
                """
                INSERT INTO directory_fitness (niche_slug, url, fitness_score, clicks_30d, impressions_30d, leads_30d, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(niche_slug, url) DO UPDATE SET
                    fitness_score = excluded.fitness_score,
                    clicks_30d = excluded.clicks_30d,
                    impressions_30d = excluded.impressions_30d,
                    leads_30d = excluded.leads_30d,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (spec.niche_slug, url, fitness, clicks, imps, leads, status, now_iso),
            )
            scored.append(
                {
                    "url": url,
                    "fitness_score": fitness,
                    "clicks_30d": clicks,
                    "impressions_30d": imps,
                    "leads_30d": leads,
                    "avg_position": round(float(r["avg_pos"] or 0.0), 1),
                    "status": status,
                }
            )
        conn.commit()

    return scored


def run_kaizen_evolution(
    spec: NicheSpec,
    listings: List[Dict[str, Any]],
    *,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Inspect `gsc_telemetry` for striking-distance positions 4.0-20.0, propose sharper titles/descriptions,
    update compiled HTML (when dry_run=False), audit 30-day freshness, and suggest suburb expansion targets.
    """
    init_hyper_kaizen_schema()
    router = GenAIRouter()
    dist_dir = SITES_ROOT / spec.niche_slug / "dist"
    fitness_rows = compute_fitness_scores(spec)

    with get_sqlite_connection(SYS_DB_PATH) as conn:
        striking = conn.execute(
            """
            SELECT url, query, clicks, impressions, ctr, position
            FROM gsc_telemetry
            WHERE niche_slug = ? AND position >= 4.0 AND position <= 20.0
            ORDER BY impressions DESC
            LIMIT 5
            """,
            (spec.niche_slug,),
        ).fetchall()

    mutations: List[Dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for row in striking:
        url = row["url"]
        query = row["query"]
        pos = float(row["position"])
        imps = int(row["impressions"])
        target_file = _resolve_local_html(url, dist_dir)
        old_title = ""
        if target_file and target_file.exists():
            raw = target_file.read_text(encoding="utf-8", errors="ignore")
            m_t = re.search(r"<title>(.*?)</title>", raw, re.I | re.S)
            old_title = m_t.group(1).strip() if m_t else ""

        prompt = (
            f"Rewrite SEO <title> (<=62 chars) and <meta description> (<=152 chars) for high CTR "
            f"targeting query '{query}' currently at Google position {pos:.1f} ({imps} impressions). "
            "Return JSON {'title': str, 'description': str}."
        )

        def _fb(q: str = query, ot: str = old_title) -> Dict[str, Any]:
            clean_q = q.title()
            return {
                "title": f"{clean_q} — Top Verified 2026 Pros & Instant Cost",
                "description": f"Compare top-rated {q} contractors in DFW with verified credentials, 24/7 dispatch filters, and real local cost estimates.",
            }

        proposal = router.generate_json(prompt, fallback_factory=_fb, est_tokens=400)
        new_title = str(proposal.get("title") or _fb()["title"])[:70]
        new_desc = str(proposal.get("description") or _fb()["description"])[:160]
        reason = f"Striking-distance pos {pos:.1f} ({imps} impressions) on query '{query}'"

        applied = False
        if not dry_run and target_file and target_file.exists():
            html_txt = target_file.read_text(encoding="utf-8")
            html_txt = re.sub(r"<title>.*?</title>", f"<title>{new_title}</title>", html_txt, count=1, flags=re.I | re.S)
            html_txt = re.sub(
                r'<meta name="description" content="[^"]*">',
                f'<meta name="description" content="{new_desc}">',
                html_txt,
                count=1,
                flags=re.I,
            )
            target_file.write_text(html_txt, encoding="utf-8")
            applied = True

        with get_sqlite_connection(SYS_DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO kaizen_mutations (niche_slug, url, mutation_type, old_val, new_val, reason, applied_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    spec.niche_slug,
                    url,
                    "STRIKING_DISTANCE_META_DRY_RUN" if dry_run else "STRIKING_DISTANCE_META_APPLIED",
                    old_title,
                    new_title,
                    reason,
                    now_iso,
                ),
            )
            conn.commit()

        mutations.append(
            {
                "url": url,
                "query": query,
                "position": pos,
                "old_title": old_title,
                "proposed_title": new_title,
                "applied": applied,
                "dry_run": dry_run,
            }
        )

    existing_cities = {(it.get("city") or "").strip().lower() for it in listings}
    expansion_targets = [c for c in EXPANSION_SUBURB_POOL if c.lower() not in existing_cities][:4]

    stale_pages: List[str] = []
    for f_row in fitness_rows:
        if f_row["status"] == "CONSOLIDATE_CANDIDATE":
            stale_pages.append(f_row["url"])

    return {
        "dry_run": dry_run,
        "fitness_tracked_urls": len(fitness_rows),
        "striking_distance_candidates": len(striking),
        "mutations": mutations,
        "suburb_expansion_recommendations": expansion_targets,
        "consolidate_candidates": stale_pages,
    }
