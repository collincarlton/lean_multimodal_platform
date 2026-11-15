#!/usr/bin/env python3
"""
Loop 2 — Deep Refinery & Technical Audit Crossover.
Harvests real listings (enforcing zero synthetic 555-xxxx records), runs MemoryBudgetGuard-protected
website crawls with strict 3s network barriers, executes Two-Pass GenAI enrichment in 5-item batches,
and pipes broken/leaky contractor websites straight into Engine 2 `prospect_audits`.
"""

from __future__ import annotations

import asyncio
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .core_guard import (
    ENGINE_DB_PATH,
    SYS_DB_PATH,
    GenAIRouter,
    MemoryBudgetGuard,
    get_sqlite_connection,
    init_hyper_kaizen_schema,
)
from .demand_scout import NicheSpec

FAKE_PHONE_RE = re.compile(r"555[-.\s]?\d{4}")
CHAT_FINGERPRINTS = ("tidio", "podium", "birdeye", "leadconnector", "intercom", "drift", "chat-widget", "twilio")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def slugify(text: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return clean or "item"


def _is_valid_real_phone(phone: Optional[str]) -> bool:
    if not phone:
        return True
    return not bool(FAKE_PHONE_RE.search(phone))


def _ensure_enrichment_columns() -> None:
    """Safely migrate new Hyper-Kaizen columns onto engine1.db listings & enrichments tables."""
    with get_sqlite_connection(ENGINE_DB_PATH) as conn:
        l_cols = {r["name"] for r in conn.execute("PRAGMA table_info(listings)").fetchall()}
        if "completeness_score" not in l_cols:
            conn.execute("ALTER TABLE listings ADD COLUMN completeness_score REAL DEFAULT 0.0")
        if "tech_audit_json" not in l_cols:
            conn.execute("ALTER TABLE listings ADD COLUMN tech_audit_json TEXT DEFAULT '{}'")
        e_cols = {r["name"] for r in conn.execute("PRAGMA table_info(enrichments)").fetchall()}
        for col, ddl in [
            ("crane_rigging", "INTEGER DEFAULT 0"),
            ("isa_certified", "INTEGER DEFAULT 0"),
            ("commercial_accounts", "INTEGER DEFAULT 0"),
            ("free_estimate", "INTEGER DEFAULT 0"),
            ("lead_readiness_score", "REAL DEFAULT 0.0"),
            ("speed_to_lead_latency_sec", "REAL DEFAULT 0.0"),
        ]:
            if col not in e_cols:
                conn.execute(f"ALTER TABLE enrichments ADD COLUMN {col} {ddl}")
        conn.commit()


class _SiteProbeParser(HTMLParser):
    """Lightweight stdlib HTML probe checking viewport, tel:, form, .pdf traps, and visible text."""

    def __init__(self) -> None:
        super().__init__()
        self.has_viewport = False
        self.has_tel = False
        self.has_form = False
        self.has_pdf = False
        self._skip_depth = 0
        self.text_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if t in ("script", "style", "noscript"):
            self._skip_depth += 1
        elif t == "meta" and attr_map.get("name", "").lower() == "viewport":
            self.has_viewport = True
        elif t == "form":
            self.has_form = True
        elif t == "a":
            href = attr_map.get("href", "").strip()
            if href.lower().startswith("tel:"):
                self.has_tel = True
            if re.search(r"\.pdf(\?|$)", href, re.I):
                self.has_pdf = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("script", "style", "noscript") and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)


def inspect_website_fast(url: Optional[str], timeout_sec: float = 3.0) -> Dict[str, Any]:
    """
    Lightweight technical + evidence probe with strict <=3s network timeout (mobile hotspot safe).
    Extracts Filter-Gap evidence AND broken-site friction signals for Engine 2 crossover.
    """
    if not url or not str(url).startswith(("http://", "https://")):
        return {
            "status": "NO_WEBSITE",
            "ssl": False,
            "viewport": False,
            "has_tel_link": False,
            "has_form": False,
            "has_chat": False,
            "has_pdf_trap": False,
            "ttfb_ms": 0.0,
            "evidence_text": "",
            "pain_points": ["Missing dedicated website (losing direct organic & AI search leads)"],
            "pain_score": 65.0,
        }

    parsed = urllib.parse.urlparse(url)
    ssl_active = parsed.scheme == "https"
    t0 = time.perf_counter()
    req = urllib.request.Request(url, headers=HEADERS)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec, context=ctx) as resp:
            raw_bytes = resp.read(180_000)
            ttfb_ms = round((time.perf_counter() - t0) * 1000.0, 1)
            html_raw = raw_bytes.decode("utf-8", errors="ignore")
            html_lower = html_raw.lower()
            probe = _SiteProbeParser()
            probe.feed(html_raw)

            has_viewport = probe.has_viewport
            has_tel = probe.has_tel
            has_form = probe.has_form
            has_chat = any(fp in html_lower for fp in CHAT_FINGERPRINTS)
            has_pdf_trap = probe.has_pdf and not has_form

            visible_text = " ".join(probe.text_parts)[:3500]
            pain_points: List[str] = []
            pain_score = 0.0
            if not ssl_active:
                pain_points.append("No HTTPS/SSL certificate (browser security warning)")
                pain_score += 25.0
            if not has_viewport:
                pain_points.append("Missing mobile viewport tag (broken smartphone layout)")
                pain_score += 22.0
            if not has_tel:
                pain_points.append("No clickable tel: emergency call link")
                pain_score += 18.0
            if not has_chat and not has_form:
                pain_points.append("No instant quote form or SMS/chat capture widget")
                pain_score += 22.0
            elif not has_chat:
                pain_points.append("No automated 60-second speed-to-lead SMS/chat responder")
                pain_score += 15.0
            if has_pdf_trap:
                pain_points.append("Static PDF quote/intake trap instead of structured intake form")
                pain_score += 18.0
            if ttfb_ms > 2200:
                pain_points.append(f"Slow server TTFB ({ttfb_ms:.0f} ms > 2,200 ms threshold)")
                pain_score += 15.0

            return {
                "status": "ACTIVE",
                "ssl": ssl_active,
                "viewport": has_viewport,
                "has_tel_link": has_tel,
                "has_form": has_form,
                "has_chat": has_chat,
                "has_pdf_trap": has_pdf_trap,
                "ttfb_ms": ttfb_ms,
                "evidence_text": visible_text,
                "pain_points": pain_points,
                "pain_score": min(100.0, round(pain_score, 1)),
            }
    except ssl.SSLError:
        return {
            "status": "SSL_BROKEN",
            "ssl": False,
            "viewport": False,
            "has_tel_link": False,
            "has_form": False,
            "has_chat": False,
            "has_pdf_trap": False,
            "ttfb_ms": round((time.perf_counter() - t0) * 1000.0, 1),
            "evidence_text": "",
            "pain_points": ["Broken SSL/TLS handshake blocking Chrome & Safari visitors"],
            "pain_score": 82.0,
        }
    except Exception as exc:
        return {
            "status": f"UNREACHABLE_{type(exc).__name__}",
            "ssl": ssl_active,
            "viewport": False,
            "has_tel_link": False,
            "has_form": False,
            "has_chat": False,
            "has_pdf_trap": False,
            "ttfb_ms": round((time.perf_counter() - t0) * 1000.0, 1),
            "evidence_text": "",
            "pain_points": [f"Website timeout/error within 3s barrier ({type(exc).__name__})"],
            "pain_score": 74.0,
        }


def _heuristic_enrich(row: Dict[str, Any], evidence: str, spec: NicheSpec) -> Dict[str, Any]:
    """Deterministic grounded extraction from listing fields + crawled website text."""
    blob = f"{row.get('business_name','')} {row.get('address','')} {evidence}".lower()
    city = row.get("city") or "Dallas"
    emergency = 1 if any(k in blob for k in ("24/7", "24 hour", "emergency", "storm", "same day", "same-week")) else 0
    crane = 1 if any(k in blob for k in ("crane", "rigging", "bucket truck", "aerial", "polyaspartic", "steel pier", "urethane")) else 0
    isa = 1 if any(k in blob for k in ("isa", "certified", "arborist", "diamond", "pe stamp", "engineered", "licensed")) else 0
    commercial = 1 if any(k in blob for k in ("commercial", "hoa", "municipal", "warehouse", "fleet", "multi-family")) else 0
    free_est = 1 if any(k in blob for k in ("free estimate", "free quote", "free inspection", "no-obligation")) else 0
    rating = float(row.get("rating") or 0.0)
    reviews = int(row.get("reviews_count") or 0)

    active_labels = [
        f["label"]
        for f, flag in zip(spec.filter_gap_facets, [emergency, crane, isa, commercial, free_est])
        if flag
    ]
    service_str = ", ".join(active_labels) if active_labels else f"{spec.category}, Free On-Site Inspection"
    badges = []
    if rating >= 4.8 and reviews >= 15:
        badges.append("Top Rated 4.8+")
    if emergency:
        badges.append("24/7 Rapid Dispatch")
    if isa:
        badges.append("Verified Credential")

    summary = (
        f"{row['business_name']} serves {city}, {row.get('state','TX')} with specialized {spec.category.lower()} services"
        + (f", featuring {service_str.lower()}." if service_str else ".")
    )
    return {
        "business_name": row["business_name"],
        "summary": summary,
        "services_offered": service_str,
        "emergency_24_7": emergency,
        "crane_rigging": crane,
        "isa_certified": isa,
        "commercial_accounts": commercial,
        "free_estimate": free_est,
        "badges": ", ".join(badges),
        "price_tier": "$$$" if crane and commercial else "$$",
    }


def _compute_completeness(row: Dict[str, Any], enriched: Dict[str, Any]) -> float:
    checks = [
        bool(row.get("business_name")),
        bool(row.get("phone")) and _is_valid_real_phone(row.get("phone")),
        bool(row.get("city")),
        bool(row.get("address")),
        bool(row.get("website")),
        bool(enriched.get("summary")),
        bool(enriched.get("services_offered")),
        (row.get("rating") or 0) > 0,
    ]
    return round((sum(1 for c in checks if c) / len(checks)) * 100.0, 1)


def _record_prospect_audit(row: Dict[str, Any], audit: Dict[str, Any], niche_slug: str) -> None:
    """Pipe broken/leaky listing sites directly into prospect_audits in both DBs."""
    if audit.get("pain_score", 0.0) < 35.0:
        return
    company = row["business_name"]
    c_slug = slugify(company)
    now_iso = datetime.now(timezone.utc).isoformat()
    bottlenecks = json.dumps(audit.get("pain_points", []))
    summary = (
        f"{company} ({row.get('city', 'DFW')}) exhibits {len(audit.get('pain_points', []))} "
        f"lead-leak bottlenecks: {'; '.join(audit.get('pain_points', [])[:2])}."
    )
    # Score higher ICP for commercial operators with established review velocity
    icp = min(98.0, round(50.0 + min(30.0, float(row.get("reviews_count") or 0) * 0.25) + (audit["pain_score"] * 0.2), 1))

    with get_sqlite_connection(SYS_DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO prospect_audits
            (company_name, company_slug, website, city, niche, source_directory, audit_summary, bottlenecks_json, pain_score, icp_score, outreach_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DIRECTORY_CROSSOVER_READY', ?)
            ON CONFLICT(company_slug) DO UPDATE SET
                audit_summary = excluded.audit_summary,
                bottlenecks_json = excluded.bottlenecks_json,
                pain_score = excluded.pain_score,
                icp_score = excluded.icp_score,
                source_directory = excluded.source_directory
            """,
            (
                company,
                c_slug,
                row.get("website") or "",
                row.get("city") or "Dallas",
                niche_slug,
                niche_slug,
                summary,
                bottlenecks,
                audit["pain_score"],
                icp,
                now_iso,
            ),
        )
        conn.commit()

    with get_sqlite_connection(ENGINE_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prospect_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                url TEXT,
                audit_date TEXT NOT NULL,
                ttfb_ms REAL,
                mobile_responsive INTEGER,
                pdf_trap INTEGER,
                speed_to_lead_score INTEGER,
                doc_url TEXT,
                local_mirror_path TEXT,
                raw_payload TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT INTO prospect_audits
            (company_name, slug, url, audit_date, ttfb_ms, mobile_responsive, pdf_trap, speed_to_lead_score, raw_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                ttfb_ms = excluded.ttfb_ms,
                mobile_responsive = excluded.mobile_responsive,
                pdf_trap = excluded.pdf_trap,
                speed_to_lead_score = excluded.speed_to_lead_score,
                raw_payload = excluded.raw_payload
            """,
            (
                company,
                c_slug,
                row.get("website") or "",
                datetime.now(timezone.utc).date().isoformat(),
                float(audit.get("ttfb_ms") or 0.0),
                1 if audit.get("viewport") else 0,
                1 if audit.get("has_pdf_trap") else 0,
                max(10, int(100 - audit.get("pain_score", 0.0))),
                json.dumps({"source_directory": niche_slug, "icp_score": icp, "pain_points": audit.get("pain_points", [])}),
            ),
        )
        conn.commit()


def refine_niche_listings(
    spec: NicheSpec,
    *,
    target_count: int = 100,
    crawl_limit: int = 15,
    use_genai: bool = True,
) -> Dict[str, Any]:
    """
    Load real verified contractors for `spec`, inspect a bounded subset of websites under 3s barrier
    + MemoryBudgetGuard, pack 5-item Two-Pass enrichment batches, and persist normalized enrichments.
    Returns summary dict + list of hydrated listing dicts.
    """
    init_hyper_kaizen_schema()
    _ensure_enrichment_columns()
    guard = MemoryBudgetGuard(max_concurrent_tabs=2, recycle_every_n_urls=25, min_available_mb=900.0)
    router = GenAIRouter()

    with get_sqlite_connection(ENGINE_DB_PATH) as conn:
        niche_row = conn.execute("SELECT id FROM niches WHERE name = ?", (spec.db_name,)).fetchone()
        if not niche_row:
            return {"niche_id": None, "listings": [], "audits_queued": 0, "memory": guard.get_memory_stats()}
        niche_id = int(niche_row["id"])

        rows = conn.execute(
            """
            SELECT l.*, e.summary, e.services_offered, e.emergency_24_7, e.crane_rigging,
                   e.isa_certified, e.commercial_accounts, e.free_estimate, e.badges, e.price_tier
            FROM listings l
            LEFT JOIN enrichments e ON e.listing_id = l.id
            WHERE l.niche_id = ?
            ORDER BY COALESCE(l.reviews_count, 0) DESC, COALESCE(l.rating, 0) DESC, l.id ASC
            LIMIT ?
            """,
            (niche_id, target_count),
        ).fetchall()

    listings: List[Dict[str, Any]] = []
    rejected_fake = 0
    audits_queued = 0
    crawled = 0
    pending_enrich: List[Tuple[Dict[str, Any], str]] = []

    raw_items: List[Dict[str, Any]] = []
    to_crawl_indices: List[int] = []
    for r in rows:
        item = dict(r)
        if not _is_valid_real_phone(item.get("phone")):
            rejected_fake += 1
            continue
        try:
            tech_audit = json.loads(item.get("tech_audit_json") or "{}")
        except Exception:
            tech_audit = {}
        item["tech_audit"] = tech_audit
        idx = len(raw_items)
        raw_items.append(item)
        if (not tech_audit or crawl_limit >= target_count) and len(to_crawl_indices) < crawl_limit:
            to_crawl_indices.append(idx)

    if to_crawl_indices:
        from concurrent.futures import ThreadPoolExecutor

        guard.check_memory_pressure()
        urls_to_probe = [(idx, raw_items[idx].get("website")) for idx in to_crawl_indices]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for idx, audit_res in zip(
                [u[0] for u in urls_to_probe],
                pool.map(lambda pair: inspect_website_fast(pair[1], timeout_sec=3.0), urls_to_probe),
            ):
                raw_items[idx]["tech_audit"] = audit_res
                guard.note_url_processed()
                crawled += 1

    for item in raw_items:
        tech_audit = item.get("tech_audit") or {}
        if tech_audit.get("pain_score", 0.0) >= 35.0:
            _record_prospect_audit(item, tech_audit, spec.niche_slug)
            audits_queued += 1

        evidence_text = tech_audit.get("evidence_text", "")
        if not item.get("summary") or item.get("is_enriched") == 0:
            pending_enrich.append((item, evidence_text))
        else:
            item["completeness_score"] = _compute_completeness(item, item)
        listings.append(item)

    # Batch pack remaining items (5 items per call) into GenAIRouter
    enriched_count = 0
    if pending_enrich:
        for batch in router.pack_batches(pending_enrich, batch_size=5):
            batch_evidence = "\n".join(
                f"[{i+1}] {it['business_name']} | City: {it.get('city')} | Website: {it.get('website')} | Evidence: {ev[:600]}"
                for i, (it, ev) in enumerate(batch)
            )
            prompt = (
                f"For the niche '{spec.db_name}', classify ONLY facts supported by the evidence below into "
                "JSON object {'items': [{'business_name': str, 'summary': str, 'services_offered': str, "
                "'emergency_24_7': 0|1, 'crane_rigging': 0|1, 'isa_certified': 0|1, "
                "'commercial_accounts': 0|1, 'free_estimate': 0|1, 'badges': str, 'price_tier': '$$'|'$$$'}]}."
            )

            def _fallback_batch(b: List[Tuple[Dict[str, Any], str]] = batch) -> Dict[str, Any]:
                return {"items": [_heuristic_enrich(it, ev, spec) for it, ev in b]}

            if use_genai:
                res = router.generate_json(
                    prompt,
                    two_pass_evidence=batch_evidence,
                    fallback_factory=_fallback_batch,
                    est_tokens=900,
                )
            else:
                res = _fallback_batch()

            by_name = {x.get("business_name", "").lower(): x for x in res.get("items", []) if isinstance(x, dict)}
            now_iso = datetime.now(timezone.utc).isoformat()
            with get_sqlite_connection(ENGINE_DB_PATH) as conn:
                for it, ev in batch:
                    enr = by_name.get(it["business_name"].lower()) or _heuristic_enrich(it, ev, spec)
                    it.update(enr)
                    it["completeness_score"] = _compute_completeness(it, enr)
                    conn.execute(
                        "UPDATE listings SET is_enriched = 1, completeness_score = ?, tech_audit_json = ? WHERE id = ?",
                        (it["completeness_score"], json.dumps({k: v for k, v in it["tech_audit"].items() if k != "evidence_text"}), it["id"]),
                    )
                    existing_e = conn.execute("SELECT id FROM enrichments WHERE listing_id = ?", (it["id"],)).fetchone()
                    if existing_e:
                        conn.execute(
                            """
                            UPDATE enrichments SET
                                summary = ?, services_offered = ?, emergency_24_7 = ?,
                                crane_rigging = ?, isa_certified = ?, commercial_accounts = ?,
                                free_estimate = ?, badges = ?, price_tier = ?, enriched_at = ?
                            WHERE listing_id = ?
                            """,
                            (
                                enr["summary"], enr["services_offered"], int(enr.get("emergency_24_7", 0)),
                                int(enr.get("crane_rigging", 0)), int(enr.get("isa_certified", 0)),
                                int(enr.get("commercial_accounts", 0)), int(enr.get("free_estimate", 0)),
                                enr.get("badges", ""), enr.get("price_tier", "$$"), now_iso, it["id"],
                            ),
                        )
                    else:
                        conn.execute(
                            """
                            INSERT INTO enrichments
                            (listing_id, summary, services_offered, emergency_24_7, badges, price_tier, schema_org_json, enriched_at,
                             crane_rigging, isa_certified, commercial_accounts, free_estimate)
                            VALUES (?, ?, ?, ?, ?, ?, '{}', ?, ?, ?, ?, ?)
                            """,
                            (
                                it["id"], enr["summary"], enr["services_offered"], int(enr.get("emergency_24_7", 0)),
                                enr.get("badges", ""), enr.get("price_tier", "$$"), now_iso,
                                int(enr.get("crane_rigging", 0)), int(enr.get("isa_certified", 0)),
                                int(enr.get("commercial_accounts", 0)), int(enr.get("free_estimate", 0)),
                            ),
                        )
                    enriched_count += 1
                conn.commit()
    else:
        # Persist any newly collected tech_audit summaries + completeness scores
        with get_sqlite_connection(ENGINE_DB_PATH) as conn:
            for it in listings:
                if it.get("tech_audit"):
                    clean_audit = {k: v for k, v in it["tech_audit"].items() if k != "evidence_text"}
                    conn.execute(
                        "UPDATE listings SET completeness_score = ?, tech_audit_json = ? WHERE id = ?",
                        (it.get("completeness_score", 0.0), json.dumps(clean_audit), it["id"]),
                    )
            conn.commit()

    return {
        "niche_id": niche_id,
        "count": len(listings),
        "rejected_fake": rejected_fake,
        "crawled": crawled,
        "recycle_count": guard.recycle_count,
        "enriched_new": enriched_count,
        "audits_queued": audits_queued,
        "memory": guard.get_memory_stats(),
        "listings": listings,
    }
