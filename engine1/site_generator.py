#!/usr/bin/env python3
"""
ENGINE-1: High-Speed Static Directory Site Generator
Target: macOS Darwin x86_64 (APFS Fusion Drive)
Output: lean_multimodal_platform/docs/ (Ready for 1-Click GitHub Pages)
Architecture: Two-Column Responsive Layout (Tailwind CSS CDN + CSS Grid + Vanilla JS Filter Engine)
SEO: Complete Schema.org/ItemList JSON-LD + sitemap.xml + robots.txt
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import jinja2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SiteGen] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("SiteGen")

HOME_DIR = Path.home().resolve()
HOME_DEV = HOME_DIR.stat().st_dev
PLATFORM_DIR = Path("/Users/collincarlton/lean_multimodal_platform").resolve()
DATA_DIR = PLATFORM_DIR / "data"
DB_PATH = DATA_DIR / "engine1.db"
DOCS_DIR = PLATFORM_DIR / "docs"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ niche.name }} | DFW Verified 24/7 Arborist & Crane Removal Network</title>
    <meta name="description" content="Direct dispatch directory for emergency tree removal, crane-assisted arborist felling, and storm damage recovery across Dallas, Fort Worth, Plano, Arlington, and North Texas.">
    
    <!-- OpenGraph / Social Meta -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="{{ niche.name }} - DFW 24/7 Emergency Directory">
    <meta property="og:description" content="Connect instantly with {{ total_count }} verified ISA certified arborists and crane tree removal crews in North Texas.">
    <meta property="og:site_name" content="DFW Arborist Dispatch">
    
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        forest: { 800: '#1e3a2f', 900: '#142921' },
                        amber: { 400: '#fbbf24', 500: '#f59e0b' }
                    }
                }
            }
        }
    </script>
    
    <!-- Schema.org ItemList JSON-LD -->
    <script type="application/ld+json">
    {{ schema_item_list_json | safe }}
    </script>

    <style>
        .pulse-beacon {
            animation: beacon 2s cubic-bezier(0, 0, 0.2, 1) infinite;
        }
        @keyframes beacon {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 antialiased min-h-screen flex flex-col">

    <!-- Top Emergency Announcement Bar -->
    <div class="bg-emerald-900 text-white text-xs sm:text-sm font-medium py-2 px-4 border-b border-emerald-700/60 sticky top-0 z-40 backdrop-blur shadow-sm">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <div class="flex items-center space-x-2">
                <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 pulse-beacon"></span>
                <span><strong>LIVE DISPATCH:</strong> 24/7 Severe Storm & Crane Tree Operations Active Across DFW Metroplex</span>
            </div>
            <div class="hidden md:flex items-center space-x-4 text-emerald-200">
                <span>Zero Booking Fees</span>
                <span>•</span>
                <span>Direct Contractor Calling</span>
            </div>
        </div>
    </div>

    <!-- Header Section -->
    <header class="bg-white border-b border-slate-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <div class="flex items-center space-x-2 text-emerald-700 font-bold tracking-wide uppercase text-xs mb-1">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>
                        <span>Sovereign Local Directory MVP (Engine-1)</span>
                    </div>
                    <h1 class="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
                        {{ niche.name }}
                    </h1>
                    <p class="mt-2 text-base sm:text-lg text-slate-600 max-w-3xl">
                        Instant directory of <strong>{{ total_count }}</strong> verified crane arborists, hazardous tree surgeons, and 24/7 storm damage crews in North Texas.
                    </p>
                </div>
                <div class="flex items-center space-x-3 bg-emerald-50 border border-emerald-200 rounded-xl p-4 shrink-0">
                    <div class="text-right">
                        <div class="text-2xl font-black text-emerald-900">{{ total_count }}</div>
                        <div class="text-xs text-emerald-700 font-semibold uppercase">Verified Pros</div>
                    </div>
                    <div class="w-px h-10 bg-emerald-200"></div>
                    <div class="text-left">
                        <div class="text-2xl font-black text-emerald-900">100%</div>
                        <div class="text-xs text-emerald-700 font-semibold uppercase">Direct Call</div>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Two-Column Directory Workspace -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

            <!-- LEFT COLUMN: Filter & Search Sidebar (Sticky on Desktop) -->
            <aside class="lg:col-span-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm sticky top-16 space-y-6">
                <div>
                    <h2 class="text-lg font-bold text-slate-900 flex items-center justify-between">
                        <span>Directory Filters</span>
                        <button id="reset-filters" class="text-xs font-semibold text-emerald-600 hover:text-emerald-800 underline">Reset</button>
                    </h2>
                    <p class="text-xs text-slate-500 mt-1">Refine {{ total_count }} contractors by service, city, or rating</p>
                </div>

                <!-- Search Input -->
                <div class="space-y-1.5">
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-700">Keyword Search</label>
                    <div class="relative">
                        <input id="search-input" type="text" placeholder="Search by name, city, service..." 
                            class="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition">
                        <svg class="w-4 h-4 text-slate-400 absolute left-3 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                    </div>
                </div>

                <!-- City Select Filter -->
                <div class="space-y-1.5">
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-700">Metro Municipality</label>
                    <select id="city-filter" class="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition bg-white">
                        <option value="ALL">All DFW Cities ({{ total_count }})</option>
                        {% for city, count in city_counts.items() %}
                        <option value="{{ city }}">{{ city }} ({{ count }})</option>
                        {% endfor %}
                    </select>
                </div>

                <!-- 24/7 Emergency Toggle -->
                <div class="pt-2 border-t border-slate-100">
                    <label class="flex items-center justify-between cursor-pointer group">
                        <div>
                            <div class="text-sm font-bold text-slate-900 group-hover:text-emerald-700 transition">24/7 Emergency Dispatch</div>
                            <div class="text-xs text-slate-500">Only show active storm crews</div>
                        </div>
                        <input id="emergency-toggle" type="checkbox" class="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500 cursor-pointer">
                    </label>
                </div>

                <!-- Minimum Rating Filter -->
                <div class="space-y-2 pt-2 border-t border-slate-100">
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-700">Customer Rating</label>
                    <div class="grid grid-cols-3 gap-2">
                        <button data-min-rating="0" class="rating-btn active py-2 text-xs font-bold rounded-lg border border-emerald-600 bg-emerald-50 text-emerald-800 transition">All</button>
                        <button data-min-rating="4.8" class="rating-btn py-2 text-xs font-bold rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition">4.8+ ★</button>
                        <button data-min-rating="5.0" class="rating-btn py-2 text-xs font-bold rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition">5.0 ★</button>
                    </div>
                </div>

                <!-- Live Results Summary Box -->
                <div class="bg-slate-50 rounded-xl p-4 border border-slate-200 text-center">
                    <div class="text-xs uppercase font-bold text-slate-500">Matching Listings</div>
                    <div id="results-count" class="text-2xl font-black text-slate-900 mt-0.5">{{ total_count }}</div>
                    <div class="text-xs text-slate-500 mt-1">Verified DFW Tree Specialists</div>
                </div>
            </aside>

            <!-- RIGHT COLUMN: Responsive Listings Grid -->
            <section class="lg:col-span-8 space-y-4">
                <div class="flex items-center justify-between pb-2 border-b border-slate-200">
                    <span class="text-sm font-semibold text-slate-600">Showing verified contractors</span>
                    <span class="text-xs text-slate-400">Direct Contact • No Middleman Fees</span>
                </div>

                <!-- Listings Container -->
                <div id="listings-container" class="space-y-4">
                    {% for item in listings %}
                    <article class="listing-card bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition duration-200 group relative"
                        data-name="{{ item.business_name | lower }}"
                        data-city="{{ item.city }}"
                        data-rating="{{ item.rating }}"
                        data-emergency="{{ item.emergency_24_7 }}"
                        data-summary="{{ item.summary | lower }}"
                        data-services="{{ item.services_offered | lower }}">
                        
                        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                            <!-- Business Info -->
                            <div class="space-y-1.5 flex-1">
                                <div class="flex flex-wrap items-center gap-2">
                                    <h3 class="text-xl font-bold text-slate-900 group-hover:text-emerald-700 transition">
                                        {{ item.business_name }}
                                    </h3>
                                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                                        {{ item.city }}, TX
                                    </span>
                                    <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-600">
                                        {{ item.price_tier }}
                                    </span>
                                </div>

                                <!-- Rating & Reviews -->
                                <div class="flex items-center space-x-2 text-sm text-slate-600">
                                    <div class="flex text-amber-400">
                                        ★ {{ item.rating }}
                                    </div>
                                    <span class="text-slate-300">•</span>
                                    <span>({{ item.reviews_count }} verified reviews)</span>
                                    <span class="text-slate-300">•</span>
                                    {% if item.emergency_24_7 == 1 %}
                                    <span class="inline-flex items-center text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 pulse-beacon"></span>
                                        24/7 Emergency Dispatch
                                    </span>
                                    {% else %}
                                    <span class="text-xs text-slate-500">Standard Business Hours</span>
                                    {% endif %}
                                </div>

                                <!-- Summary -->
                                <p class="text-sm text-slate-600 mt-2 leading-relaxed">
                                    {{ item.summary }}
                                </p>

                                <!-- Trust Badges -->
                                <div class="flex flex-wrap gap-1.5 pt-2">
                                    {% for badge in item.badges_list %}
                                    <span class="text-[11px] font-semibold bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md border border-slate-200">
                                        ✓ {{ badge }}
                                    </span>
                                    {% endfor %}
                                </div>
                            </div>

                            <!-- Action Directives Column -->
                            <div class="flex flex-col sm:items-end gap-2 shrink-0 pt-2 sm:pt-0">
                                <a href="tel:{{ item.phone }}" 
                                    class="inline-flex items-center justify-center space-x-2 px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-sm hover:shadow transition w-full sm:w-auto">
                                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 4V3z"></path></svg>
                                    <span>{{ item.phone }}</span>
                                </a>

                                <div class="flex items-center space-x-2 w-full sm:w-auto">
                                    {% if item.website and item.website != 'N/A' %}
                                    <a href="{{ item.website }}" target="_blank" rel="noopener noreferrer"
                                        class="flex-1 sm:flex-none text-center px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition">
                                        Visit Website ↗
                                    </a>
                                    {% endif %}
                                    <button onclick="openSchemaModal({{ item.id }})"
                                        class="flex-1 sm:flex-none px-3 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700 transition">
                                        View Schema
                                    </button>
                                </div>
                            </div>
                        </div>
                    </article>
                    {% endfor %}
                </div>

                <!-- Empty State -->
                <div id="no-results" class="hidden text-center py-16 bg-white rounded-2xl border border-slate-200 p-8">
                    <svg class="w-12 h-12 text-slate-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <h4 class="text-base font-bold text-slate-800">No matching arborists found</h4>
                    <p class="text-sm text-slate-500 mt-1">Try relaxing your search terms or resetting filters.</p>
                </div>
            </section>
        </div>
    </main>

    <!-- Schema Modal -->
    <div id="schema-modal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[85vh] flex flex-col">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="text-lg font-bold text-slate-900">Schema.org JSON-LD (Search Engine Spec)</h3>
                <button onclick="closeSchemaModal()" class="text-slate-400 hover:text-slate-600 font-bold text-xl">&times;</button>
            </div>
            <pre id="modal-json-content" class="bg-slate-900 text-emerald-400 p-4 rounded-xl text-xs overflow-auto font-mono flex-1"></pre>
            <div class="flex justify-end space-x-3 pt-2">
                <button onclick="copySchemaJson()" id="copy-btn" class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition">Copy JSON-LD</button>
                <button onclick="closeSchemaModal()" class="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-xs font-bold hover:bg-slate-50 transition">Close</button>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-white border-t border-slate-200 py-8 mt-12 text-center text-xs text-slate-500">
        <div class="max-w-7xl mx-auto px-4 space-y-2">
            <p><strong>{{ niche.name }}</strong> — High-Performance Programmatic Directory (Engine-1 Autonomous MVP).</p>
            <p>Zero Capital Autonomous Build • APFS Barrier Compliant • Verified Local Data.</p>
            <div class="flex justify-center space-x-4 pt-2 text-slate-400">
                <a href="sitemap.xml" class="hover:text-slate-600 underline">XML Sitemap</a>
                <span>•</span>
                <a href="robots.txt" class="hover:text-slate-600 underline">robots.txt</a>
                <span>•</span>
                <span>Generated: {{ generated_at }}</span>
            </div>
        </div>
    </footer>

    <!-- Client-Side Filter Script -->
    <script>
        const listingsData = {{ raw_listings_json | safe }};
        const searchInput = document.getElementById('search-input');
        const cityFilter = document.getElementById('city-filter');
        const emergencyToggle = document.getElementById('emergency-toggle');
        const ratingButtons = document.querySelectorAll('.rating-btn');
        const resultsCount = document.getElementById('results-count');
        const cards = document.querySelectorAll('.listing-card');
        const noResults = document.getElementById('no-results');
        const resetBtn = document.getElementById('reset-filters');
        
        let currentMinRating = 0;

        function applyFilters() {
            const query = searchInput.value.trim().toLowerCase();
            const selectedCity = cityFilter.value;
            const emergencyOnly = emergencyToggle.checked;
            let visibleCount = 0;

            cards.forEach(card => {
                const name = card.dataset.name;
                const city = card.dataset.city;
                const rating = parseFloat(card.dataset.rating) || 0;
                const isEmergency = card.dataset.emergency === '1';
                const summary = card.dataset.summary;
                const services = card.dataset.services;

                let matchesQuery = !query || name.includes(query) || city.toLowerCase().includes(query) || summary.includes(query) || services.includes(query);
                let matchesCity = (selectedCity === 'ALL') || (city === selectedCity);
                let matchesEmergency = !emergencyOnly || isEmergency;
                let matchesRating = rating >= currentMinRating;

                if (matchesQuery && matchesCity && matchesEmergency && matchesRating) {
                    card.classList.remove('hidden');
                    visibleCount++;
                } else {
                    card.classList.add('hidden');
                }
            });

            resultsCount.textContent = visibleCount;
            if (visibleCount === 0) {
                noResults.classList.remove('hidden');
            } else {
                noResults.classList.add('hidden');
            }
        }

        searchInput.addEventListener('input', applyFilters);
        cityFilter.addEventListener('change', applyFilters);
        emergencyToggle.addEventListener('change', applyFilters);

        ratingButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                ratingButtons.forEach(b => {
                    b.classList.remove('active', 'border-emerald-600', 'bg-emerald-50', 'text-emerald-800');
                    b.classList.add('border-slate-200', 'bg-white', 'text-slate-700');
                });
                btn.classList.add('active', 'border-emerald-600', 'bg-emerald-50', 'text-emerald-800');
                btn.classList.remove('border-slate-200', 'bg-white', 'text-slate-700');
                currentMinRating = parseFloat(btn.dataset.minRating) || 0;
                applyFilters();
            });
        });

        resetBtn.addEventListener('click', () => {
            searchInput.value = '';
            cityFilter.value = 'ALL';
            emergencyToggle.checked = false;
            currentMinRating = 0;
            ratingButtons.forEach((b, i) => {
                if (i === 0) {
                    b.classList.add('active', 'border-emerald-600', 'bg-emerald-50', 'text-emerald-800');
                    b.classList.remove('border-slate-200', 'bg-white', 'text-slate-700');
                } else {
                    b.classList.remove('active', 'border-emerald-600', 'bg-emerald-50', 'text-emerald-800');
                    b.classList.add('border-slate-200', 'bg-white', 'text-slate-700');
                }
            });
            applyFilters();
        });

        // Modal Logic
        let activeSchemaStr = '';
        function openSchemaModal(listingId) {
            const item = listingsData.find(l => l.id === listingId);
            if (!item) return;
            const modal = document.getElementById('schema-modal');
            const pre = document.getElementById('modal-json-content');
            try {
                const parsed = JSON.parse(item.schema_org_json);
                activeSchemaStr = JSON.stringify(parsed, null, 2);
            } catch(e) {
                activeSchemaStr = item.schema_org_json;
            }
            pre.textContent = activeSchemaStr;
            modal.classList.remove('hidden');
        }

        function closeSchemaModal() {
            document.getElementById('schema-modal').classList.add('hidden');
        }

        function copySchemaJson() {
            navigator.clipboard.writeText(activeSchemaStr).then(() => {
                const btn = document.getElementById('copy-btn');
                btn.textContent = 'Copied!';
                setTimeout(() => { btn.textContent = 'Copy JSON-LD'; }, 2000);
            });
        }
    </script>
</body>
</html>
"""


def generate_sitemap_xml(listings: List[Dict[str, Any]], base_url: str = "https://collincarlton.github.io/lean_multimodal_platform") -> str:
    """Generate clean Google-compliant XML sitemap."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url>',
        f'    <loc>{base_url}/</loc>',
        f'    <lastmod>{today}</lastmod>',
        '    <changefreq>daily</changefreq>',
        '    <priority>1.0</priority>',
        '  </url>',
    ]

    for item in listings:
        slug = item["business_name"].lower().replace(" ", "-").replace("&", "and")
        xml_lines.extend([
            '  <url>',
            f'    <loc>{base_url}/#{slug}</loc>',
            f'    <lastmod>{today}</lastmod>',
            '    <changefreq>weekly</changefreq>',
            '    <priority>0.8</priority>',
            '  </url>',
        ])

    xml_lines.append('</urlset>')
    return "\n".join(xml_lines)


def generate_robots_txt(base_url: str = "https://collincarlton.github.io/lean_multimodal_platform") -> str:
    """Generate standard robots.txt permitting all crawlers and pointing to sitemap."""
    return f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""


def build_static_directory(limit: int = 100) -> Dict[str, Any]:
    """Compile database records into static docs/ directory ready for GitHub Pages."""
    import sqlite3

    assert PLATFORM_DIR.stat().st_dev == HOME_DEV, "Mount barrier violated"
    assert DB_PATH.exists(), f"Database not found at {DB_PATH}"

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # 1. Fetch Selected Niche
    c.execute("SELECT id, name, aov_estimate, target_queries FROM niches WHERE selected = 1 LIMIT 1;")
    niche_row = c.fetchone()
    if not niche_row:
        raise RuntimeError("No selected niche found in engine1.db")
    niche = {
        "id": niche_row[0],
        "name": niche_row[1],
        "aov": niche_row[2],
        "queries": json.loads(niche_row[3]),
    }

    # 2. Fetch Top Enriched Listings
    c.execute(
        f"""
        SELECT 
            l.id, l.business_name, l.phone, l.website, l.rating, l.reviews_count, 
            l.address, l.city, l.state, l.zip_code,
            e.summary, e.services_offered, e.emergency_24_7, e.badges, e.price_tier, e.schema_org_json
        FROM listings l
        JOIN enrichments e ON l.id = e.listing_id
        ORDER BY l.rating DESC, l.reviews_count DESC
        LIMIT {limit};
        """
    )
    rows = c.fetchall()
    conn.close()

    if not rows:
        raise RuntimeError("No enriched listings found to generate directory site.")

    listings: List[Dict[str, Any]] = []
    city_counts: Dict[str, int] = {}
    schema_items: List[Dict[str, Any]] = []

    for idx, r in enumerate(rows):
        badges_list = json.loads(r[13]) if r[13] else []
        services_list = json.loads(r[11]) if r[11] else []
        city = r[7]
        city_counts[city] = city_counts.get(city, 0) + 1

        item = {
            "id": r[0],
            "business_name": r[1],
            "phone": r[2],
            "website": r[3],
            "rating": r[4],
            "reviews_count": r[5],
            "address": r[6],
            "city": city,
            "state": r[8],
            "zip_code": r[9],
            "summary": r[10],
            "services_offered": r[11],
            "services_list": services_list,
            "emergency_24_7": r[12],
            "badges": r[13],
            "badges_list": badges_list,
            "price_tier": r[14],
            "schema_org_json": r[15],
        }
        listings.append(item)

        # Build ItemList Entry
        try:
            local_schema = json.loads(r[15])
            schema_items.append({
                "@type": "ListItem",
                "position": idx + 1,
                "item": local_schema,
            })
        except Exception:
            pass

    # Sort city counts descending
    city_counts = dict(sorted(city_counts.items(), key=lambda x: x[1], reverse=True))

    schema_item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{niche['name']} Directory - North Texas DFW",
        "description": "Verified directory of top-rated emergency crane arborists and tree removal specialists.",
        "numberOfItems": len(schema_items),
        "itemListElement": schema_items,
    }

    raw_listings_json = json.dumps([
        {
            "id": item["id"],
            "business_name": item["business_name"],
            "city": item["city"],
            "schema_org_json": item["schema_org_json"],
        }
        for item in listings
    ])

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Render Template
    template = jinja2.Template(HTML_TEMPLATE)
    rendered_html = template.render(
        niche=niche,
        listings=listings,
        total_count=len(listings),
        city_counts=city_counts,
        schema_item_list_json=json.dumps(schema_item_list),
        raw_listings_json=raw_listings_json,
        generated_at=now_str,
    )

    # Write files to docs/
    index_path = DOCS_DIR / "index.html"
    index_path.write_text(rendered_html, encoding="utf-8")
    logger.info(f"Generated {index_path} ({len(rendered_html.encode('utf-8')):,} bytes)")

    sitemap_path = DOCS_DIR / "sitemap.xml"
    sitemap_content = generate_sitemap_xml(listings)
    sitemap_path.write_text(sitemap_content, encoding="utf-8")
    logger.info(f"Generated {sitemap_path}")

    robots_path = DOCS_DIR / "robots.txt"
    robots_content = generate_robots_txt()
    robots_path.write_text(robots_content, encoding="utf-8")
    logger.info(f"Generated {robots_path}")

    return {
        "status": "success",
        "docs_dir": str(DOCS_DIR),
        "total_listings": len(listings),
        "index_bytes": len(rendered_html.encode("utf-8")),
    }


def main():
    parser = argparse.ArgumentParser(description="ENGINE-1 Static Directory Site Generator")
    parser.add_argument("--limit", type=int, default=100, help="Number of listings to compile into site")
    args = parser.parse_args()

    result = build_static_directory(args.limit)
    print(f"\n[✓] Successfully generated static site: {result['docs_dir']} ({result['total_listings']} listings)")


if __name__ == "__main__":
    main()
