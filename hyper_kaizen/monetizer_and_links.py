#!/usr/bin/env python3
"""
Loop 7 — Zero-Capital Monetizer, Backlink Harvester & Engine 1 -> Engine 2 Crossover.
1. Free-Lead-First Pitch Router: identifies top active contractors and drafts $149/mo Featured upgrade pitches.
2. >=4.8* Embeddable HTML Badge Generator: builds dofollow/brand badge snippets for authority backlinks.
3. Engine 1 -> Engine 2 Audit Crossover: fetches broken-site operators queued in `prospect_audits`
   so Engine 2 can target them with Paid AI Assessment & custom Google Docs.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .core_guard import HOME_DIR, SYS_DB_PATH, assert_safe_device, get_sqlite_connection
from .deep_refinery import slugify
from .demand_scout import NicheSpec

AUDITS_DIR = HOME_DIR / "lean_multimodal_platform" / "audits"


def run_monetizer_and_links(spec: NicheSpec, listings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate $149/mo Free-Lead-First outreach, >=4.8* badge HTML, and pull Engine 2 crossover queue."""
    AUDITS_DIR.mkdir(parents=True, exist_ok=True)
    assert_safe_device(AUDITS_DIR)

    # 1. Free-Lead-First top providers (highest review velocity & verified credentials)
    featured_candidates = [
        it for it in listings
        if float(it.get("rating") or 0) >= 4.5 and int(it.get("reviews_count") or 0) >= 15
    ][:5]

    badge_candidates = [
        it for it in listings
        if float(it.get("rating") or 0) >= 4.8 and int(it.get("reviews_count") or 0) >= 10
    ][:6]

    pitch_sections: List[str] = [
        f"# Monetizer & Backlink Pack — {spec.title}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Part 1: Free-Lead-First -> $149/mo Featured Upgrade Outreach",
    ]
    for it in featured_candidates:
        city = it.get("city") or "DFW"
        pitch_sections.append(
            f"### {it['business_name']} ({city}) — {it.get('rating')}★ ({it.get('reviews_count')} reviews)\n"
            f"- **Target Phone/Site**: {it.get('phone') or 'N/A'} | {it.get('website') or 'N/A'}\n"
            f"- **Free-Lead-First Pitch**: \"Hi team at {it['business_name']} — homeowners in {city} are already clicking your verified listing on our {spec.title}. Once your listing hits 2+ routed leads this month, we can lock the #1 Featured top-of-grid slot in {city} for $149/mo (first 2 leads sent upfront free to prove ROI). Want me to send the tracking link?\"\n"
        )

    pitch_sections.append("## Part 2: Verified >=4.8★ Embeddable Badge Snippets (Backlink Flywheel)")
    sample_badges: List[Dict[str, str]] = []
    for it in badge_candidates:
        l_slug = slugify(it["business_name"])
        badge_snippet = (
            f'<a href="{spec.base_url}/listings/{l_slug}.html" target="_blank" rel="noopener" '
            f'style="display:inline-flex;align-items:center;gap:8px;padding:8px 14px;border-radius:8px;'
            f'background:#0f172a;color:#34d399;font:600 13px system-ui,sans-serif;text-decoration:none;'
            f'border:1px solid #059669;">&#9733; Verified {float(it.get("rating") or 4.8):.1f}★ Top {html.escape(spec.category)} '
            f'&mdash; {html.escape(it["business_name"])}</a>'
        )
        sample_badges.append({"business_name": it["business_name"], "badge_html": badge_snippet})
        pitch_sections.append(
            f"### {it['business_name']} ({it.get('rating')}★)\n```html\n{badge_snippet}\n```\n"
        )

    # 3. Read Engine 1 -> Engine 2 prospect_audits queued during Loop 2
    with get_sqlite_connection(SYS_DB_PATH) as conn:
        crossover_rows = conn.execute(
            """
            SELECT company_name, city, website, pain_score, icp_score, bottlenecks_json, outreach_status
            FROM prospect_audits
            WHERE source_directory = ? OR niche = ?
            ORDER BY pain_score DESC, icp_score DESC
            LIMIT 10
            """,
            (spec.niche_slug, spec.niche_slug),
        ).fetchall()

    crossover_list = [dict(r) for r in crossover_rows]
    pitch_sections.append("## Part 3: Engine 1 -> Engine 2 Broken-Site Audit Crossover Targets")
    for cr in crossover_list:
        try:
            pts = ", ".join(json.loads(cr.get("bottlenecks_json") or "[]")[:2])
        except Exception:
            pts = ""
        pitch_sections.append(
            f"- **{cr['company_name']}** ({cr['city']}) | Pain `{cr['pain_score']}` | ICP `{cr['icp_score']}` | Status `{cr['outreach_status']}` | Bottlenecks: {pts}"
        )

    pack_path = AUDITS_DIR / f"monetizer_{spec.niche_slug}.md"
    pack_path.write_text("\n".join(pitch_sections), encoding="utf-8")

    return {
        "featured_upgrade_candidates": len(featured_candidates),
        "badge_outreach_candidates": len(badge_candidates),
        "crossover_audits_ready": len(crossover_list),
        "monetizer_pack_path": str(pack_path),
        "sample_badge": sample_badges[0] if sample_badges else None,
    }
