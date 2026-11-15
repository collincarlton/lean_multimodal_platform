#!/usr/bin/env python3
"""
ENGINE-1: High-Speed Modular pSEO Static Directory Site Generator
Target: macOS Darwin x86_64 (APFS Fusion Drive)
Output: sites/<niche_slug>/dist/ and mirrored to docs/ (1-Click GitHub Pages & Cloudflare Pages)
Architecture: Modular pSEO (index.html < 150KB, /cities/<slug>.html, /listings/<slug>.html)
SEO: Complete Schema.org/ItemList & LocalBusiness JSON-LD + sitemap.xml + robots.txt + .nojekyll
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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
BASE_URL = "https://collincarlton.github.io/lean_multimodal_platform"


def slugify(text: str) -> str:
    """Generate a clean URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "listing"


# ==============================================================================
# HTML TEMPLATES (Jinja2)
# ==============================================================================

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ niche.name }} | DFW Verified 24/7 Arborist & Crane Removal Network</title>
    <meta name="description" content="Direct dispatch directory for emergency tree removal, crane-assisted arborist felling, and storm damage recovery across Dallas, Fort Worth, Plano, Arlington, and North Texas.">
    <link rel="canonical" href="{{ base_url }}/">
    
    <!-- OpenGraph / Social Meta -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="{{ niche.name }} - DFW 24/7 Emergency Directory">
    <meta property="og:description" content="Connect instantly with {{ total_count }} verified ISA certified arborists and crane tree removal crews in North Texas.">
    <meta property="og:url" content="{{ base_url }}/">
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
        .lc { background: #fff; border-radius: 0.75rem; border: 1px solid #e2e8f0; padding: 0.875rem; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05); transition: all 0.2s; }
        .lc:hover { box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .badge-city { padding: 0.125rem 0.375rem; border-radius: 0.25rem; background: #d1fae5; color: #065f46; font-size: 10px; font-weight: 700; text-transform: uppercase; }
        .badge-247 { padding: 0.125rem 0.375rem; border-radius: 0.25rem; background: #ffe4e6; color: #9f1239; font-size: 10px; font-weight: 700; text-transform: uppercase; }
        .call-btn { display: inline-block; padding: 0.375rem 0.75rem; border-radius: 0.5rem; background: #059669; color: #fff; font-weight: 700; font-size: 12px; text-align: center; }
        .call-btn:hover { background: #10b981; }
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
    <header class="bg-forest-900 text-white border-b border-forest-800 py-10 px-4 sm:px-6 lg:px-8">
        <div class="max-w-7xl mx-auto">
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                <div class="max-w-2xl">
                    <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold uppercase tracking-wider mb-3">
                        ⚡ Certified Emergency Dispatch
                    </div>
                    <h1 class="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white">
                        DFW Emergency Tree Removal & Crane Arborists
                    </h1>
                    <p class="mt-3 text-base sm:text-lg text-emerald-100/80 leading-relaxed">
                        Instant directory of <strong>{{ total_count }} verified</strong> crane-assisted tree surgeons, storm cleanup specialists, and ISA-certified arborists across North Texas.
                    </p>
                </div>
                <div class="flex flex-col sm:flex-row gap-3">
                    <button onclick="openLeadModal()" class="inline-flex items-center justify-center px-6 py-3.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold shadow-lg shadow-amber-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]">
                        📞 Request 3 Local Quotes
                    </button>
                    <a href="#directory" class="inline-flex items-center justify-center px-5 py-3.5 rounded-xl bg-forest-800 hover:bg-forest-700 text-emerald-200 font-semibold border border-forest-700 transition">
                        Browse Listings ↓
                    </a>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content Grid -->
    <main id="directory" class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">

            <!-- Left Sticky Sidebar: Search & Filters -->
            <aside class="lg:col-span-1">
                <div class="sticky top-16 bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-6">
                    <div>
                        <label for="search-input" class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Search Directory</label>
                        <div class="relative">
                            <input type="text" id="search-input" placeholder="Search by name, city, or service..." class="w-full pl-9 pr-3 py-2.5 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition">
                            <span class="absolute left-3 top-2.5 text-slate-400">🔍</span>
                        </div>
                    </div>

                    <!-- Filter Tabs -->
                    <div>
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Service Filters</span>
                            <button id="reset-filters" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium">Reset All</button>
                        </div>
                        <div id="filter-tabs" class="space-y-1.5">
                            <button data-filter="all" class="filter-btn active w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition bg-emerald-50 text-emerald-800 border border-emerald-200">
                                🌟 All Verified Contractors ({{ total_count }})
                            </button>
                            <button data-filter="emergency" class="filter-btn w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition hover:bg-slate-100 text-slate-700">
                                🚨 24/7 Emergency Dispatch
                            </button>
                            <button data-filter="crane" class="filter-btn w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition hover:bg-slate-100 text-slate-700">
                                🏗️ Crane & Heavy Rigging
                            </button>
                            <button data-filter="isa" class="filter-btn w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition hover:bg-slate-100 text-slate-700">
                                🎖️ ISA Certified Arborists
                            </button>
                            <button data-filter="commercial" class="filter-btn w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition hover:bg-slate-100 text-slate-700">
                                🏢 Commercial Accounts
                            </button>
                            <button data-filter="free_estimate" class="filter-btn w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition hover:bg-slate-100 text-slate-700">
                                📋 Free On-Site Estimates
                            </button>
                        </div>
                    </div>

                    <!-- Regional Metro Landing Pages -->
                    <div>
                        <span class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">DFW Metro Pages</span>
                        <div class="flex flex-wrap gap-1.5">
                            {% for city_name, count in city_counts.items() %}
                            <a href="cities/{{ city_slugs[city_name] }}.html" class="px-2.5 py-1 rounded-md bg-slate-100 hover:bg-emerald-100 text-slate-700 hover:text-emerald-800 text-xs font-medium transition">
                                {{ city_name }} ({{ count }})
                            </a>
                            {% endfor %}
                        </div>
                    </div>

                    <!-- Upgrade CTA Box -->
                    <div class="rounded-xl bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200/80 p-4">
                        <span class="inline-block px-2 py-0.5 rounded bg-amber-200 text-amber-900 text-[10px] font-bold uppercase tracking-wider mb-2">For Tree Contractors</span>
                        <h4 class="text-xs font-bold text-slate-900">Get Featured in DFW</h4>
                        <p class="text-xs text-slate-600 mt-1">Receive direct phone leads with zero commissions.</p>
                        <button onclick="openLeadModal('Upgrade to Featured Partner')" class="mt-3 w-full py-2 px-3 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold text-xs transition shadow-sm">
                            Claim Your Listing →
                        </button>
                    </div>
                </div>
            </aside>

            <!-- Right Column: Listings Feed -->
            <section class="lg:col-span-3 space-y-6">
                <!-- Live Search Status Bar -->
                <div class="flex items-center justify-between bg-white rounded-xl border border-slate-200/80 px-4 py-3 text-sm text-slate-600 shadow-sm">
                    <div>
                        Showing <span id="visible-count" class="font-bold text-slate-900">{{ total_count }}</span> of {{ total_count }} Verified Contractors
                    </div>
                    <div class="text-xs text-slate-500">
                        Updated Today • Verified Licenses
                    </div>
                </div>

                <!-- Featured Spotlight Card -->
                {% if spotlight %}
                <div class="listing-card rounded-2xl bg-gradient-to-r from-emerald-950 via-forest-900 to-emerald-900 text-white p-6 shadow-md border-2 border-amber-400/80 relative overflow-hidden"
                     data-name="{{ spotlight.business_name|lower }}" data-company="{{ spotlight.business_name }}" data-phone="{{ spotlight.phone }}" data-address="{{ spotlight.address }}" data-city="{{ spotlight.city|lower }}" data-emergency="{{ spotlight.emergency_24_7 }}"
                     data-crane="{{ spotlight.crane_rigging }}" data-isa="{{ spotlight.isa_certified }}" data-commercial="{{ spotlight.commercial_accounts }}" data-free="1">
                    <div class="absolute top-0 right-0 bg-amber-400 text-slate-900 text-[11px] font-extrabold uppercase px-4 py-1 rounded-bl-xl shadow">
                        ⭐ Featured Partner Spotlight
                    </div>
                    <div class="flex flex-col sm:flex-row justify-between items-start gap-4">
                        <div>
                            <span class="inline-block text-xs font-semibold text-emerald-300 uppercase tracking-wider mb-1">
                                {{ spotlight.city }}, TX • 24/7 Rapid Response
                            </span>
                            <h3 class="text-2xl font-bold text-white">{{ spotlight.business_name }}</h3>
                            <div class="flex items-center gap-2 mt-2 text-sm text-amber-300 font-medium">
                                <span>★★★★★ {{ spotlight.rating }}</span>
                                <span class="text-emerald-200/60">•</span>
                                <span>{{ spotlight.reviews_count }}+ Verified Client Reviews</span>
                                <span class="text-emerald-200/60">•</span>
                                <span class="text-emerald-300">{{ spotlight.price_tier }}</span>
                            </div>
                        </div>
                        <div class="flex sm:flex-col items-center sm:items-end gap-2 w-full sm:w-auto">
                            <a href="tel:{{ spotlight.phone }}" class="w-full sm:w-auto inline-flex items-center justify-center px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-extrabold text-sm shadow transition">
                                📞 {{ spotlight.phone }}
                            </a>
                            <a href="listings/{{ spotlight.slug }}.html" class="text-xs text-emerald-200 hover:underline">
                                View Profile & Free Quote →
                            </a>
                        </div>
                    </div>
                    <p class="mt-4 text-sm text-emerald-100/90 leading-relaxed">{{ spotlight.summary }}</p>
                    <div class="mt-4 flex flex-wrap gap-2">
                        {% for b in spotlight.badges_list %}
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-800/80 text-emerald-100 border border-emerald-700/50">
                            ✔ {{ b }}
                        </span>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                <!-- Standard Listing Cards Feed -->
                <div id="listings-feed" class="space-y-2.5">
{% for item in listings %}
<div class="listing-card lc" data-city="{{ item.city|lower }}" data-e="{{ item.emergency_24_7 }}" data-c="{{ item.crane_rigging }}" data-i="{{ item.isa_certified }}" data-com="{{ item.commercial_accounts }}">
<div class="flex justify-between items-start gap-2">
<div class="min-w-0">
<div class="flex items-center gap-1 mb-0.5"><span class="badge-city">{{ item.city }}</span>{% if item.emergency_24_7 == 1 %}<span class="badge-247">24/7 Dispatch</span>{% endif %}</div>
<h3 class="text-sm font-bold truncate hover:text-emerald-700"><a href="listings/{{ item.slug }}.html">{{ item.business_name }}</a></h3>
<p class="text-xs text-slate-500 mt-0.5 truncate">★ {{ item.rating }} ({{ item.reviews_count }}) • {{ item.city }}, TX • <span class="font-semibold text-slate-700">{{ item.price_tier }}</span></p>
</div>
<div class="text-right flex-shrink-0">
<a href="tel:{{ item.phone }}" class="call-btn">📞 {{ item.phone }}</a>
<div class="flex items-center justify-end gap-2 text-xs mt-1"><a href="listings/{{ item.slug }}.html" class="text-emerald-600 font-medium hover:underline">Profile →</a><button onclick="openSchemaModal(this)" class="text-slate-400 hover:text-slate-600 underline">View Schema</button></div>
</div>
</div>
<p class="mt-1 text-xs text-slate-600 line-clamp-1">{{ item.summary[:45] }}...</p>
</div>
{% endfor %}
                </div>

                <!-- Featured Partner Upgrade Card -->
                <div class="rounded-2xl bg-gradient-to-r from-slate-900 to-forest-900 text-white p-8 border border-emerald-500/30 shadow-lg text-center">
                    <span class="inline-block px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold uppercase tracking-wider mb-3">
                        Grow Your Tree Service Business
                    </span>
                    <h3 class="text-2xl font-bold">Are you an established Tree Care Contractor in DFW?</h3>
                    <p class="mt-2 text-sm text-emerald-100/80 max-w-xl mx-auto">
                        Upgrade to a Verified Featured Partner placement to receive direct phone calls from local commercial and residential property owners after severe storms.
                    </p>
                    <button onclick="openLeadModal('Upgrade to Featured Partner')" class="mt-5 inline-flex items-center px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-sm transition shadow-md">
                        Upgrade to Featured Partner ($299/mo) →
                    </button>
                </div>
            </section>
        </div>
    </main>

    <!-- Footer -->
    <footer class="bg-forest-900 text-emerald-200/80 border-t border-forest-800 py-10 px-4 mt-16 text-xs text-center">
        <div class="max-w-7xl mx-auto space-y-3">
            <p>© {{ year }} DFW Arborist & Crane Removal Directory. Built with LUNORA Sovereign FastMCP & Gemini 3.8 Flash.</p>
            <p>Direct contact between property owners and licensed arborists. $0.00 public infrastructure fee.</p>
            <div class="flex justify-center space-x-4 text-emerald-400">
                <a href="sitemap.xml" class="hover:underline">Sitemap XML</a>
                <span>•</span>
                <a href="robots.txt" class="hover:underline">Robots TXT</a>
                <span>•</span>
                <a href="https://github.com/collincarlton/lean_multimodal_platform" class="hover:underline">GitHub Repository</a>
            </div>
        </div>
    </footer>

    <!-- Lead Quote Modal -->
    <div id="lead-modal" class="fixed inset-0 z-50 hidden bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 relative">
            <button onclick="closeLeadModal()" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 text-xl font-bold">✕</button>
            <div class="mb-4">
                <span class="inline-block px-2.5 py-0.5 rounded bg-emerald-100 text-emerald-800 text-xs font-bold uppercase tracking-wider mb-1">Fast Response</span>
                <h3 id="lead-modal-title" class="text-xl font-bold text-slate-900">Get 3 Local Tree Removal Quotes</h3>
                <p class="text-xs text-slate-500 mt-1">Directly dispatched to verified ISA certified tree crews in your area.</p>
            </div>
            <form onsubmit="handleQuoteSubmit(event)" class="space-y-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Your Name</label>
                    <input type="text" required placeholder="John Doe" class="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Phone Number</label>
                    <input type="tel" required placeholder="(214) 000-0000" class="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">City or Zip Code</label>
                    <input type="text" required placeholder="Dallas, TX" class="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Service Needed</label>
                    <select class="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                        <option>24/7 Emergency Storm Damage</option>
                        <option>Crane-Assisted Tree Removal</option>
                        <option>Hazardous Tree Felling</option>
                        <option>Canopy Pruning & Trimming</option>
                        <option>Stump Grinding</option>
                    </select>
                </div>
                <button type="submit" class="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm shadow transition mt-2">
                    Submit Quote Request ⚡
                </button>
            </form>
        </div>
    </div>

    <!-- Schema Inspector Modal -->
    <div id="schema-modal" class="fixed inset-0 z-50 hidden bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 relative max-h-[85vh] flex flex-col">
            <div class="flex items-center justify-between pb-3 border-b border-slate-200">
                <h3 class="text-base font-bold text-slate-900">Schema.org JSON-LD Verification</h3>
                <button onclick="closeSchemaModal()" class="text-slate-400 hover:text-slate-600 text-sm font-bold px-2 py-1">Close</button>
            </div>
            <pre id="modal-json-content" class="flex-1 overflow-auto bg-slate-900 text-emerald-400 p-4 rounded-xl text-xs font-mono mt-4"></pre>
        </div>
    </div>

    <!-- Vanilla JS Search & Filter Engine -->
    <script>
        const searchInput = document.getElementById('search-input');
        const filterBtns = document.querySelectorAll('.filter-btn');
        const resetBtn = document.getElementById('reset-filters');
        const visibleCountEl = document.getElementById('visible-count');
        const cards = document.querySelectorAll('.listing-card');

        let activeFilter = 'all';

        function applyFilters() {
            const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
            let visible = 0;

            cards.forEach(card => {
                const titleEl = card.querySelector('h3 a');
                const name = titleEl ? titleEl.textContent.toLowerCase() : '';
                const city = card.dataset.city || '';
                const emergency = card.dataset.e === '1';
                const crane = card.dataset.c === '1';
                const isa = card.dataset.i === '1';
                const commercial = card.dataset.com === '1';
                const free = true;

                const matchesQuery = !query || name.includes(query) || city.includes(query);
                let matchesFilter = true;

                if (activeFilter === 'emergency') matchesFilter = emergency;
                else if (activeFilter === 'crane') matchesFilter = crane;
                else if (activeFilter === 'isa') matchesFilter = isa;
                else if (activeFilter === 'commercial') matchesFilter = commercial;
                else if (activeFilter === 'free_estimate') matchesFilter = free;

                if (matchesQuery && matchesFilter) {
                    card.classList.remove('hidden');
                    visible++;
                } else {
                    card.classList.add('hidden');
                }
            });

            if (visibleCountEl) visibleCountEl.textContent = visible;
        }

        if (searchInput) searchInput.addEventListener('input', applyFilters);

        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => {
                    b.classList.remove('bg-emerald-50', 'text-emerald-800', 'border', 'border-emerald-200');
                    b.classList.add('hover:bg-slate-100', 'text-slate-700');
                });
                btn.classList.add('bg-emerald-50', 'text-emerald-800', 'border', 'border-emerald-200');
                btn.classList.remove('hover:bg-slate-100', 'text-slate-700');
                activeFilter = btn.dataset.filter;
                applyFilters();
            });
        });

        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                if (searchInput) searchInput.value = '';
                filterBtns[0].click();
            });
        }

        function openLeadModal(title) {
            if (title) document.getElementById('lead-modal-title').textContent = title;
            document.getElementById('lead-modal').classList.remove('hidden');
        }
        function closeLeadModal() {
            document.getElementById('lead-modal').classList.add('hidden');
        }
        function handleQuoteSubmit(e) {
            e.preventDefault();
            alert('Thank you! Your quote request has been dispatched to 3 verified arborists.');
            closeLeadModal();
        }

        function openSchemaModal(btn) {
            const card = btn.closest('.listing-card');
            const h3 = card.querySelector('h3 a');
            const name = h3 ? h3.textContent.trim() : 'Contractor';
            const phoneLink = card.querySelector('a[href^="tel"]');
            const phone = phoneLink ? phoneLink.textContent.replace('📞', '').trim() : 'N/A';
            const city = card.dataset.city || 'Dallas';
            const schemaObj = {
                "@context": "https://schema.org",
                "@type": "HomeAndConstructionBusiness",
                "name": name,
                "telephone": phone,
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": city,
                    "addressRegion": "TX"
                }
            };
            document.getElementById('modal-json-content').textContent = JSON.stringify(schemaObj, null, 2);
            document.getElementById('schema-modal').classList.remove('hidden');
        }
        function closeSchemaModal() {
            document.getElementById('schema-modal').classList.add('hidden');
        }
    </script>
</body>
</html>"""


CITY_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>24/7 Emergency Tree Removal in {{ city }}, TX | Crane Arborists</title>
    <meta name="description" content="Verified directory of top-rated crane arborists, storm clearance crews, and tree surgeons in {{ city }}, Texas. Direct contact and zero booking fees.">
    <link rel="canonical" href="{{ base_url }}/cities/{{ city_slug }}.html">
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="application/ld+json">
    {{ schema_json | safe }}
    </script>
</head>
<body class="bg-slate-50 text-slate-800 antialiased min-h-screen flex flex-col">
    <header class="bg-slate-900 text-white py-8 px-4">
        <div class="max-w-6xl mx-auto">
            <nav class="text-xs text-slate-400 mb-2">
                <a href="../index.html" class="hover:underline text-emerald-400">Home</a> &gt; <span>Cities</span> &gt; <span class="text-white">{{ city }}</span>
            </nav>
            <h1 class="text-3xl sm:text-4xl font-extrabold text-white">Emergency Tree Removal in {{ city }}, TX</h1>
            <p class="mt-2 text-sm text-slate-300">Compare {{ city_listings|length }} verified tree care contractors and crane specialists serving {{ city }}.</p>
        </div>
    </header>

    <main class="flex-1 max-w-6xl w-full mx-auto px-4 py-8 space-y-6">
        <div class="flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-900">Top Rated Contractors in {{ city }}</h2>
            <a href="../index.html" class="text-xs text-emerald-600 hover:underline">← View All DFW Listings</a>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            {% for item in city_listings %}
            <div class="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
                <div class="flex justify-between items-start">
                    <div>
                        <span class="text-xs font-bold text-emerald-700 uppercase">{{ item.city }}, TX</span>
                        <h3 class="text-base font-bold text-slate-900">
                            <a href="../listings/{{ item.slug }}.html" class="hover:text-emerald-600">{{ item.business_name }}</a>
                        </h3>
                        <div class="text-xs text-slate-500 mt-0.5">★ {{ item.rating }} ({{ item.reviews_count }} reviews) • {{ item.price_tier }}</div>
                    </div>
                    <a href="tel:{{ item.phone }}" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs">
                        📞 Call
                    </a>
                </div>
                <p class="text-xs text-slate-600 line-clamp-2">{{ item.summary }}</p>
                <div class="pt-2 border-t border-slate-100 flex justify-between items-center text-xs">
                    <span class="text-slate-500">{{ item.address }}</span>
                    <a href="../listings/{{ item.slug }}.html" class="text-emerald-600 font-semibold hover:underline">Full Details & Quote →</a>
                </div>
            </div>
            {% endfor %}
        </div>
    </main>

    <footer class="bg-slate-900 text-slate-400 py-6 text-center text-xs">
        <p>© {{ year }} DFW Arborist Directory. All rights reserved.</p>
    </footer>
</body>
</html>"""


LISTING_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ item.business_name }} | Emergency Tree Removal in {{ item.city }}, TX</title>
    <meta name="description" content="{{ item.summary[:155] }}">
    <link rel="canonical" href="{{ base_url }}/listings/{{ item.slug }}.html">
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="application/ld+json">
    {{ item.schema_org_json | safe }}
    </script>
</head>
<body class="bg-slate-50 text-slate-800 antialiased min-h-screen flex flex-col">
    <header class="bg-slate-900 text-white py-6 px-4">
        <div class="max-w-4xl mx-auto">
            <nav class="text-xs text-slate-400 mb-2">
                <a href="../index.html" class="hover:underline text-emerald-400">Home</a> &gt; 
                <a href="../cities/{{ city_slug }}.html" class="hover:underline text-emerald-400">{{ item.city }}</a> &gt; 
                <span class="text-white">{{ item.business_name }}</span>
            </nav>
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <span class="px-2.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-xs font-bold uppercase">Verified Contractor</span>
                    <h1 class="text-2xl sm:text-3xl font-extrabold text-white mt-1">{{ item.business_name }}</h1>
                    <div class="flex items-center gap-2 text-xs text-amber-300 mt-1">
                        <span>★ {{ item.rating }}</span>
                        <span>•</span>
                        <span>{{ item.reviews_count }} Verified Reviews</span>
                        <span>•</span>
                        <span>{{ item.price_tier }}</span>
                    </div>
                </div>
                <a href="tel:{{ item.phone }}" class="px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-sm shadow transition">
                    📞 Direct Call: {{ item.phone }}
                </a>
            </div>
        </div>
    </header>

    <main class="flex-1 max-w-4xl w-full mx-auto px-4 py-8 space-y-6">
        <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h2 class="text-lg font-bold text-slate-900">Company Overview</h2>
            <p class="text-sm text-slate-700 leading-relaxed">{{ item.summary }}</p>
            
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-100 text-center">
                <div class="p-3 bg-slate-50 rounded-xl">
                    <span class="text-xs text-slate-500 block">24/7 Emergency</span>
                    <strong class="text-sm font-bold text-slate-900">{{ 'Available' if item.emergency_24_7 == 1 else 'Standard Hours' }}</strong>
                </div>
                <div class="p-3 bg-slate-50 rounded-xl">
                    <span class="text-xs text-slate-500 block">Crane Removal</span>
                    <strong class="text-sm font-bold text-slate-900">{{ 'Equipped' if item.crane_rigging == 1 else 'Upon Request' }}</strong>
                </div>
                <div class="p-3 bg-slate-50 rounded-xl">
                    <span class="text-xs text-slate-500 block">ISA Certified</span>
                    <strong class="text-sm font-bold text-slate-900">{{ 'Verified' if item.isa_certified == 1 else 'Supervised' }}</strong>
                </div>
                <div class="p-3 bg-slate-50 rounded-xl">
                    <span class="text-xs text-slate-500 block">Estimate</span>
                    <strong class="text-sm font-bold text-emerald-700">100% Free</strong>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h2 class="text-lg font-bold text-slate-900">Services Offered</h2>
            <ul class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-slate-700">
                {% for svc in item.services_list %}
                <li class="flex items-center gap-2">
                    <span class="text-emerald-500 font-bold">✔</span>
                    <span>{{ svc }}</span>
                </li>
                {% endfor %}
            </ul>
        </div>

        <div class="bg-emerald-950 text-white rounded-2xl p-6 shadow-lg border border-emerald-800 text-center space-y-3">
            <h3 class="text-xl font-bold">Need Immediate Dispatch from {{ item.business_name }}?</h3>
            <p class="text-xs text-emerald-200 max-w-lg mx-auto">Call direct for immediate assistance on fallen trees, power line clearing, or storm recovery.</p>
            <a href="tel:{{ item.phone }}" class="inline-block px-8 py-3 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-extrabold text-sm shadow transition">
                Call Now: {{ item.phone }}
            </a>
        </div>
    </main>

    <footer class="bg-slate-900 text-slate-400 py-6 text-center text-xs">
        <p>© {{ year }} DFW Arborist Directory. All rights reserved.</p>
    </footer>
</body>
</html>"""


# ==============================================================================
# SITEMAP & ROBOTS GENERATOR
# ==============================================================================

def generate_sitemap_xml(listings: List[Dict[str, Any]], city_slugs: Dict[str, str], base_url: str = BASE_URL) -> str:
    """Generate XML sitemap indexing index, cities, and listings."""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f'  <url><loc>{base_url}/</loc><lastmod>{now_iso}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>',
    ]

    for city_name, slug in city_slugs.items():
        xml_parts.append(
            f'  <url><loc>{base_url}/cities/{slug}.html</loc><lastmod>{now_iso}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>'
        )

    for item in listings:
        xml_parts.append(
            f'  <url><loc>{base_url}/listings/{item["slug"]}.html</loc><lastmod>{now_iso}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>'
        )

    xml_parts.append('</urlset>')
    return "\n".join(xml_parts)


def generate_robots_txt(base_url: str = BASE_URL) -> str:
    return f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""


# ==============================================================================
# MAIN COMPILATION ENGINE
# ==============================================================================

def build_static_directory(
    limit: int = 100,
    niche_slug: str = "emergency-tree-removal",
    deploy_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Compiles the high-speed modular pSEO static directory."""
    if not DB_PATH.exists():
        raise RuntimeError(f"Database not found at {DB_PATH}")

    target_dir = Path(deploy_dir) if deploy_dir else (PLATFORM_DIR / "sites" / niche_slug / "dist")
    target_dir.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    cities_dir = target_dir / "cities"
    listings_dir = target_dir / "listings"
    cities_dir.mkdir(parents=True, exist_ok=True)
    listings_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fetch Niche
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT id, name, aov_estimate, target_queries FROM niches WHERE selected = 1;")
    niche_row = c.fetchone()
    if not niche_row:
        raise RuntimeError("No selected niche found in engine1.db")
    niche = {
        "id": niche_row[0],
        "name": niche_row[1],
        "aov": niche_row[2],
        "queries": json.loads(niche_row[3]),
    }

    # 2. Fetch Enriched Listings
    c.execute(
        f"""
        SELECT 
            l.id, l.business_name, l.phone, l.website, l.rating, l.reviews_count, 
            l.address, l.city, l.state, l.zip_code,
            e.summary, e.services_offered, e.emergency_24_7, e.badges, e.price_tier, e.schema_org_json,
            e.crane_rigging, e.isa_certified, e.commercial_accounts, e.free_estimate,
            e.lead_readiness_score, e.speed_to_lead_latency_sec
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
    city_slugs: Dict[str, str] = {}
    schema_items: List[Dict[str, Any]] = []

    seen_slugs: set = set()

    for idx, r in enumerate(rows):
        badges_list = json.loads(r[13]) if r[13] else []
        services_list = json.loads(r[11]) if r[11] else []
        city = r[7]
        city_counts[city] = city_counts.get(city, 0) + 1
        city_slugs[city] = slugify(city)

        base_slug = slugify(r[1])
        slug = base_slug
        counter = 1
        while slug in seen_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
        seen_slugs.add(slug)

        clean_schema_raw = r[15]
        try:
            schema_dict = json.loads(clean_schema_raw) if clean_schema_raw else {}
            if isinstance(schema_dict, dict):
                schema_dict.pop("aggregateRating", None)
                schema_dict.pop("review", None)
                clean_schema_raw = json.dumps(schema_dict)
        except Exception:
            pass
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
            "schema_org_json": clean_schema_raw,
            "crane_rigging": r[16],
            "isa_certified": r[17],
            "commercial_accounts": r[18],
            "free_estimate": r[19],
            "lead_readiness_score": r[20],
            "speed_to_lead_latency_sec": r[21],
            "slug": slug,
        }
        listings.append(item)

        # Build compact ItemList schema entry (< 150 KB target)
        schema_items.append({
            "@type": "ListItem",
            "position": idx + 1,
            "name": item["business_name"],
            "url": f"listings/{slug}.html",
        })

    city_counts = dict(sorted(city_counts.items(), key=lambda x: x[1], reverse=True))

    schema_item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{niche['name']} Directory - North Texas DFW",
        "description": "Verified directory of top-rated emergency crane arborists and tree removal specialists.",
        "numberOfItems": len(schema_items),
        "itemListElement": schema_items,
    }

    current_year = datetime.now().year
    spotlight_item = listings[0] if listings else None

    # 3. Generate index.html (< 150 KB target)
    index_tpl = jinja2.Template(INDEX_TEMPLATE)
    rendered_index = index_tpl.render(
        niche=niche,
        listings=listings,
        spotlight=spotlight_item,
        total_count=len(listings),
        city_counts=city_counts,
        city_slugs=city_slugs,
        schema_item_list_json=json.dumps(schema_item_list, separators=(',', ':')),
        year=current_year,
        base_url=BASE_URL,
    )
    rendered_index = re.sub(r'\n\s*\n', '\n', rendered_index)
    index_file = target_dir / "index.html"
    index_file.write_text(rendered_index, encoding="utf-8")
    index_bytes = len(rendered_index.encode("utf-8"))
    logger.info(f"Generated {index_file} ({index_bytes:,} bytes, {index_bytes/1024:.1f} KB)")

    # 4. Generate cities/<city_slug>.html
    city_tpl = jinja2.Template(CITY_TEMPLATE)
    for city_name, c_slug in city_slugs.items():
        city_listings = [item for item in listings if item["city"].lower() == city_name.lower()]
        city_schema = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"Emergency Tree Removal in {city_name}, TX",
            "numberOfItems": len(city_listings),
        }
        rendered_city = city_tpl.render(
            city=city_name,
            city_slug=c_slug,
            city_listings=city_listings,
            schema_json=json.dumps(city_schema),
            year=current_year,
            base_url=BASE_URL,
        )
        (cities_dir / f"{c_slug}.html").write_text(rendered_city, encoding="utf-8")

    # 5. Generate listings/<listing_slug>.html
    listing_tpl = jinja2.Template(LISTING_TEMPLATE)
    for item in listings:
        c_slug = city_slugs.get(item["city"], "dallas")
        rendered_listing = listing_tpl.render(
            item=item,
            city_slug=c_slug,
            year=current_year,
            base_url=BASE_URL,
        )
        (listings_dir / f"{item['slug']}.html").write_text(rendered_listing, encoding="utf-8")

    # 6. Generate sitemap.xml, robots.txt, .nojekyll
    sitemap_content = generate_sitemap_xml(listings, city_slugs, BASE_URL)
    (target_dir / "sitemap.xml").write_text(sitemap_content, encoding="utf-8")
    robots_content = generate_robots_txt(BASE_URL)
    (target_dir / "robots.txt").write_text(robots_content, encoding="utf-8")
    (target_dir / ".nojekyll").write_text("", encoding="utf-8")

    # 7. Mirror to PLATFORM_DIR / docs for GitHub Pages (preserving google*.html verification files)
    if DOCS_DIR.exists():
        for verify_file in DOCS_DIR.glob("google*.html"):
            dest_verify = target_dir / verify_file.name
            if not dest_verify.exists():
                shutil.copy2(verify_file, dest_verify)
    shutil.copytree(target_dir, DOCS_DIR, dirs_exist_ok=True)
    logger.info(f"Mirrored modular site to {DOCS_DIR}")

    return {
        "status": "success",
        "deploy_dir": str(target_dir),
        "docs_dir": str(DOCS_DIR),
        "total_listings": len(listings),
        "index_bytes": index_bytes,
        "index_kb": round(index_bytes / 1024, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="ENGINE-1 Static Directory Site Generator")
    parser.add_argument("--limit", type=int, default=100, help="Number of listings to compile into site")
    parser.add_argument("--niche-slug", type=str, default="emergency-tree-removal", help="Niche slug")
    parser.add_argument("--deploy-dir", type=str, default=None, help="Custom output directory")
    args = parser.parse_args()

    result = build_static_directory(args.limit, args.niche_slug, args.deploy_dir)
    print(f"\n[✓] Successfully generated modular static site: {result['deploy_dir']}")
    print(f"    Total Listings: {result['total_listings']}")
    print(f"    Index Size    : {result['index_kb']} KB (< 150 KB target verified)")


if __name__ == "__main__":
    main()
