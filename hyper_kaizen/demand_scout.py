#!/usr/bin/env python3
"""
Loop 1 — Niche Demand & Filter-Gap Scout.
Scores local high-ticket service niches, selects Filter-Gap facets missing on Google Maps,
and maps niche_slug <-> engine1.db niches table.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from .core_guard import ENGINE_DB_PATH, get_sqlite_connection


@dataclass
class NicheSpec:
    niche_slug: str
    db_name: str
    title: str
    category: str
    metro: str
    state: str
    aov_estimate: float
    urgency_level: str
    filter_gap_facets: List[Dict[str, str]]
    target_cities: List[str]
    calculator_config: Dict[str, Any]
    faqs: List[Dict[str, str]]
    base_url: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


NICHE_CATALOG: Dict[str, NicheSpec] = {
    "emergency-tree-dfw": NicheSpec(
        niche_slug="emergency-tree-dfw",
        db_name="Emergency Tree Removal & Crane Arborists",
        title="DFW Emergency Tree Removal & Crane Arborist Directory",
        category="Arboriculture & Tree Care",
        metro="Dallas-Fort Worth",
        state="TX",
        aov_estimate=2850.0,
        urgency_level="CRITICAL_EMERGENCY",
        filter_gap_facets=[
            {"slug": "24-7-emergency", "label": "24/7 Emergency Dispatch", "field": "emergency_24_7"},
            {"slug": "crane-rigging", "label": "Crane & Rigging Equipped", "field": "crane_rigging"},
            {"slug": "isa-certified", "label": "ISA Certified Arborist", "field": "isa_certified"},
            {"slug": "commercial-accounts", "label": "Commercial & HOA Accounts", "field": "commercial_accounts"},
            {"slug": "free-estimate", "label": "Free On-Site Estimate", "field": "free_estimate"},
        ],
        target_cities=[
            "Dallas", "Fort Worth", "Arlington", "Plano", "Frisco",
            "Irving", "Denton", "Garland", "McKinney", "Richardson",
        ],
        calculator_config={
            "title": "DFW Emergency Tree Removal & Crane Cost Estimator",
            "base_min": 450,
            "base_max": 950,
            "height_tiers": [
                {"label": "Under 30 ft (Ornamental / Small Oak)", "multiplier": 1.0},
                {"label": "30 - 60 ft (Mature Pecan / Live Oak)", "multiplier": 1.85},
                {"label": "60+ ft (Towering Cottonwood / Crane Lift)", "multiplier": 3.1},
            ],
            "addons": [
                {"id": "crane", "label": "Crane Rigging Over Roof/Powerlines", "min": 650, "max": 1400},
                {"id": "emergency", "label": "After-Hours / Storm Dispatch", "min": 250, "max": 550},
                {"id": "stump", "label": "Deep Stump Grinding & Haul-Off", "min": 180, "max": 420},
            ],
        },
        faqs=[
            {
                "q": "How fast do 24/7 emergency tree crews arrive in Dallas-Fort Worth?",
                "a": "Verified 24/7 emergency crane and storm crews in DFW typically respond within 60 to 120 minutes for roof impacts, blocked driveways, and fallen limbs after severe North Texas thunderstorms.",
            },
            {
                "q": "When is crane-assisted tree removal required instead of standard climbing?",
                "a": "Crane rigging is essential when heavy hardwoods exceed 50 feet, lean over roof trusses, pool enclosures, or energized drop lines, or exhibit compromised root plates after saturated clay soil shifts.",
            },
            {
                "q": "What should DFW homeowners verify before hiring a storm-damage arborist?",
                "a": "Confirm an active ISA Certified Arborist credential, general liability coverage ($1M+ minimum), workers compensation, and a written itemization separating structural roof stabilization from haul-off for insurance claims.",
            },
            {
                "q": "How much does emergency tree removal cost in Dallas & Fort Worth?",
                "a": "Minor limb clearing starts around $450-$850, mature 50ft oaks average $1,400-$2,600, and complex crane-rigged extractions over structures range from $2,800 to $5,500+ depending on staging access.",
            },
        ],
        base_url="https://collincarlton.github.io/lean_multimodal_platform",
    ),
    "commercial-epoxy-dfw": NicheSpec(
        niche_slug="commercial-epoxy-dfw",
        db_name="Commercial & Residential Epoxy Flooring",
        title="DFW Commercial Epoxy & Polyaspartic Flooring Directory",
        category="Flooring & Concrete Coatings",
        metro="Dallas-Fort Worth",
        state="TX",
        aov_estimate=4200.0,
        urgency_level="HIGH_INTENT",
        filter_gap_facets=[
            {"slug": "polyaspartic-1day", "label": "1-Day Polyaspartic Cure", "field": "emergency_24_7"},
            {"slug": "warehouse-forklift", "label": "Forklift-Grade Urethane", "field": "crane_rigging"},
            {"slug": "diamond-grind", "label": "CSP-3 Diamond Grind Prep", "field": "isa_certified"},
            {"slug": "commercial-accounts", "label": "Commercial & Warehouse", "field": "commercial_accounts"},
            {"slug": "free-estimate", "label": "Free Moisture & SqFt Audit", "field": "free_estimate"},
        ],
        target_cities=["Dallas", "Fort Worth", "Arlington", "Plano", "Frisco", "Irving"],
        calculator_config={
            "title": "DFW Epoxy & Polyaspartic Floor Coating Estimator",
            "base_min": 1600,
            "base_max": 2800,
            "height_tiers": [
                {"label": "2-Car Garage (~450 sq ft)", "multiplier": 1.0},
                {"label": "3-Car Garage / Shop (~850 sq ft)", "multiplier": 1.75},
                {"label": "Commercial Bay (~2,500+ sq ft)", "multiplier": 4.2},
            ],
            "addons": [
                {"id": "crane", "label": "Moisture Vapor Barrier Primer", "min": 450, "max": 900},
                {"id": "emergency", "label": "Weekend / Overnight Commercial Install", "min": 350, "max": 750},
                {"id": "stump", "label": "Crack Spall Reconstruction", "min": 250, "max": 600},
            ],
        },
        faqs=[
            {
                "q": "Why does polyaspartic floor coating outlast DIY epoxy in Texas heat?",
                "a": "100% solids polyaspartic topcoats resist UV yellowing, hot-tire pickup at 150F+ slab temperatures, and cure for light foot traffic in 4-6 hours.",
            },
            {
                "q": "Do commercial warehouses need CSP-3 diamond grinding?",
                "a": "Yes. Acid etching leaves uneven porosity; planetary diamond grinding opens the North Texas slab profile to CSP-2/CSP-3 so industrial urethane and epoxy bond mechanically.",
            },
        ],
        base_url="https://collincarlton.github.io/dfw-epoxy-directory",
    ),
    "foundation-pier-dfw": NicheSpec(
        niche_slug="foundation-pier-dfw",
        db_name="Foundation Repair & Pier Underpinning",
        title="DFW Foundation Repair & Engineered Pier Directory",
        category="Structural Engineering & Foundation",
        metro="Dallas-Fort Worth",
        state="TX",
        aov_estimate=8500.0,
        urgency_level="HIGH_TICKET",
        filter_gap_facets=[
            {"slug": "same-week-inspection", "label": "Same-Week Laser Elevation", "field": "emergency_24_7"},
            {"slug": "steel-driven-piers", "label": "Steel Driven Piers", "field": "crane_rigging"},
            {"slug": "pe-stamped", "label": "PE Stamped Engineering", "field": "isa_certified"},
            {"slug": "commercial-accounts", "label": "Commercial & Multi-Family", "field": "commercial_accounts"},
            {"slug": "free-estimate", "label": "Free Elevation Survey", "field": "free_estimate"},
        ],
        target_cities=["Dallas", "Fort Worth", "Arlington", "Plano", "Frisco", "Irving"],
        calculator_config={
            "title": "DFW Pier Underpinning Cost Estimator",
            "base_min": 3800,
            "base_max": 6400,
            "height_tiers": [
                {"label": "Perimeter Spot Stabilization (6-10 Piers)", "multiplier": 1.0},
                {"label": "Full Edge + Interior Beams (12-18 Piers)", "multiplier": 1.65},
                {"label": "Commercial / Deep Bedrock Piers (20+)", "multiplier": 2.6},
            ],
            "addons": [
                {"id": "crane", "label": "Root Barrier & French Drain", "min": 1200, "max": 2800},
                {"id": "emergency", "label": "Static Hydrostatic Plumbing Test", "min": 350, "max": 650},
                {"id": "stump", "label": "PE Stamped Closing Certificate", "min": 400, "max": 750},
            ],
        },
        faqs=[
            {
                "q": "Steel piers vs pressed concrete pilings in DFW expansive clay soil?",
                "a": "Expansive Eagle Ford and Taylor Marl clays swell and shrink seasonally; hydraulically driven steel piers reach load-bearing stratum deeper than shallow concrete cylinders.",
            },
        ],
        base_url="https://collincarlton.github.io/dfw-foundation-directory",
    ),
}


def score_niches() -> List[Dict[str, Any]]:
    """Rank Filter-Gap niches and ensure engine1.db niches rows stay synchronized."""
    results: List[Dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_sqlite_connection(ENGINE_DB_PATH) as conn:
        for idx, (slug, spec) in enumerate(NICHE_CATALOG.items(), start=1):
            filter_gap_bonus = 9.5 if len(spec.filter_gap_facets) >= 5 else 8.0
            overall = round(min(99.0, (spec.aov_estimate / 120.0) + filter_gap_bonus + (12.0 if spec.urgency_level == "CRITICAL_EMERGENCY" else 7.5)), 2)
            row = conn.execute("SELECT id FROM niches WHERE name = ?", (spec.db_name,)).fetchone()
            if not row:
                conn.execute(
                    """
                    INSERT INTO niches (name, category, aov_estimate, urgency_level, competition_score, lead_value_est, overall_score, selected, target_queries, evaluated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        spec.db_name,
                        spec.category,
                        spec.aov_estimate,
                        spec.urgency_level,
                        3.5,
                        round(spec.aov_estimate * 0.12, 2),
                        overall,
                        1 if idx == 1 else 0,
                        json.dumps([f"{spec.category} {c}" for c in spec.target_cities[:5]]),
                        now_iso,
                    ),
                )
            results.append(
                {
                    "niche_slug": slug,
                    "db_name": spec.db_name,
                    "aov_estimate": spec.aov_estimate,
                    "overall_score": overall,
                    "facet_count": len(spec.filter_gap_facets),
                }
            )
        conn.commit()
    results.sort(key=lambda r: r["overall_score"], reverse=True)
    return results


def get_niche_spec(niche_slug: str) -> NicheSpec:
    if niche_slug not in NICHE_CATALOG:
        raise KeyError(f"Unknown niche_slug '{niche_slug}'. Available: {list(NICHE_CATALOG)}")
    return NICHE_CATALOG[niche_slug]
