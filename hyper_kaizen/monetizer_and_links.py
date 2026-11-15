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

from .core_guard import ENGINE_DB_PATH, HOME_DIR, SYS_DB_PATH, assert_safe_device, get_sqlite_connection
from .deep_refinery import slugify
from .demand_scout import NicheSpec

AUDITS_DIR = HOME_DIR / "lean_multimodal_platform" / "audits"
BADGES_DIR = AUDITS_DIR / "badges"
MAX_FREE_TEASER_LEADS = 2


def get_free_lead_counts() -> Dict[str, int]:
    """Return dispatched free-teaser lead counts keyed by lowercased recipient_company."""
    counts: Dict[str, int] = {}
    for db_path in (SYS_DB_PATH, ENGINE_DB_PATH):
        try:
            with get_sqlite_connection(db_path) as conn:
                rows = conn.execute(
                    """
                    SELECT lower(trim(recipient_company)) AS comp, COUNT(*) AS cnt
                    FROM lead_dispatch_log
                    WHERE COALESCE(recipient_company, '') != ''
                    GROUP BY lower(trim(recipient_company))
                    """
                ).fetchall()
                for r in rows:
                    counts[r["comp"]] = max(counts.get(r["comp"], 0), int(r["cnt"]))
        except Exception:
            pass
    return counts


def record_lead_dispatch(
    *,
    niche_slug: str,
    city: str,
    lead_summary: str,
    recipient_company: str,
    recipient_contact: str,
    status: str = "SENT",
    outcome: str = "PENDING",
    max_free_leads: int = MAX_FREE_TEASER_LEADS,
) -> Dict[str, Any]:
    """Log lead dispatch to both DBs and evaluate 2-free-teaser-lead UPGRADE_READY threshold."""
    now_iso = datetime.now(timezone.utc).isoformat()
    counts = get_free_lead_counts()
    key = recipient_company.strip().lower()
    prior = counts.get(key, 0)
    next_count = prior + 1
    row_status = "UPGRADE_READY" if next_count >= max_free_leads else status

    for db_path in (SYS_DB_PATH, ENGINE_DB_PATH):
        with get_sqlite_connection(db_path) as conn:
            conn.execute(
                """
                INSERT INTO lead_dispatch_log
                (niche_slug, city, lead_summary, recipient_company, recipient_contact, sent_at, status, outcome)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (niche_slug, city, lead_summary, recipient_company, recipient_contact, now_iso, row_status, outcome),
            )
            conn.commit()
    return {
        "recipient_company": recipient_company,
        "leads_dispatched": next_count,
        "max_free_leads": max_free_leads,
        "upgrade_status": "UPGRADE_READY" if next_count >= max_free_leads else "FREE_TEASER_ACTIVE",
    }


def _write_badge_svg(company_name: str, rating: float, slug: str) -> Path:
    BADGES_DIR.mkdir(parents=True, exist_ok=True)
    assert_safe_device(BADGES_DIR)
    svg_path = BADGES_DIR / f"{slug}_badge.svg"
    safe_name = html.escape(company_name)[:40]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="340" height="72" viewBox="0 0 340 72">'
        '<rect width="340" height="72" rx="10" fill="#0f172a" stroke="#059669" stroke-width="2"/>'
        '<text x="16" y="28" fill="#34d399" font-family="system-ui,sans-serif" font-size="13" font-weight="700">'
        f'&#9733; {rating:.1f} Listed on DFW Arborist Dispatch</text>'
        f'<text x="16" y="50" fill="#f8fafc" font-family="system-ui,sans-serif" font-size="12" font-weight="600">{safe_name}</text>'
        '</svg>\n'
    )
    svg_path.write_text(svg, encoding="utf-8")
    return svg_path


def run_monetizer_and_links(spec: NicheSpec, listings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate Free-Lead-First (2-lead cap) outreach, Link-Spam-safe branded badges, and Engine 2 crossover queue."""
    AUDITS_DIR.mkdir(parents=True, exist_ok=True)
    assert_safe_device(AUDITS_DIR)
    lead_counts = get_free_lead_counts()

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
        f"## Part 1: Tracked Free-Lead-First -> Founding Partner Upgrade (Cap: {MAX_FREE_TEASER_LEADS} Free Leads)",
    ]
    for it in featured_candidates:
        city = it.get("city") or "DFW"
        sent = lead_counts.get(it["business_name"].strip().lower(), 0)
        flag = "UPGRADE_READY ($149/mo or $299/yr Founding Exclusive Partner)" if sent >= MAX_FREE_TEASER_LEADS else f"FREE_TEASER_ACTIVE ({sent}/{MAX_FREE_TEASER_LEADS} sent)"
        pitch_sections.append(
            f"### {it['business_name']} ({city}) — {it.get('rating')}★ ({it.get('reviews_count')} reviews) [{flag}]\n"
            f"- **Target Phone/Site**: {it.get('phone') or 'N/A'} | {it.get('website') or 'N/A'}\n"
            f"- **Tracked Pitch**: \"Hi team at {it['business_name']} — homeowners in {city} are viewing your verified profile on {spec.title}. We send up to 2 qualified homeowner inquiries free first to prove ROI; after 2 dispatched leads, you can lock the exclusive Card-on-File / Founding Partner spot for $149/mo (or $299/yr) before it opens to another crew in {city}.\"\n"
        )

    pitch_sections.append("## Part 2: Verified >=4.8★ Branded Badges (Link-Spam-Safe Anchor + Zero-HTML GBP/FB Image)")
    sample_badges: List[Dict[str, str]] = []
    for it in badge_candidates:
        l_slug = slugify(it["business_name"])
        rating_val = float(it.get("rating") or 4.8)
        svg_path = _write_badge_svg(it["business_name"], rating_val, l_slug)
        badge_snippet = (
            f'<a href="{spec.base_url}/listings/{l_slug}.html" target="_blank" rel="noopener" '
            f'style="display:inline-flex;align-items:center;gap:8px;padding:8px 14px;border-radius:8px;'
            f'background:#0f172a;color:#34d399;font:600 13px system-ui,sans-serif;text-decoration:none;'
            f'border:1px solid #059669;">Listed on DFW Arborist Dispatch</a>'
        )
        sample_badges.append({
            "business_name": it["business_name"],
            "badge_html": badge_snippet,
            "badge_svg_path": str(svg_path),
        })
        pitch_sections.append(
            f"### {it['business_name']} ({it.get('rating')}★)\n"
            f"- **Website Branded Anchor HTML:**\n```html\n{badge_snippet}\n```\n"
            f"- **Zero-HTML Facebook / Google Business Profile Image:** `{svg_path}` (Upload as post graphic with caption: `Verified {rating_val:.1f}★ — Find us via DFW Arborist Dispatch: {spec.base_url}/listings/{l_slug}.html`)\n"
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
