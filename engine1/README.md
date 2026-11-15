# ENGINE-1: Autonomous Programmatic Niche Directory MVP

Sovereign, zero-capital programmatic directory engine designed for macOS Darwin x86_64 (Intel Core i5, 8GB RAM, APFS Fusion Drive).

---

## Architecture & Operational Invariants
- **FinOps Quota Gate**: Strict **\$0.00 spend** (ZeroCapitalLaw). Zero paid SaaS, zero proxies, zero paid hosting.
- **APFS Virtual Mount Barrier**: Verified `os.stat(p).st_dev == HOME_DEV (16777223)`.
- **Storage Subsystem**: `aiosqlite` WAL mode (`journal_mode=WAL`, `synchronous=NORMAL`, `cache_size=-32000` / 32MB ceiling).
- **Harvester Memory Barrier**: Headless Playwright Chromium with resource-blocking router (aborts heavy images, fonts, and stylesheets to protect 8GB RAM).
- **Enrichment Engine**: Gemini 3.8 Flash (`gemini-3.8-flash`) free-tier integration with rate-limiting and sovereign deterministic SEO synthesis fallback.
- **Frontend / SEO Engine**: High-speed responsive two-column layout using Tailwind CSS CDN, CSS Grid, vanilla JS instant client-side filtering, and comprehensive `Schema.org/ItemList` LocalBusiness JSON-LD markup.
- **Static Hosting Target**: Pure static files written to `docs/` ready for 1-click GitHub Pages deployment.

---

## Directory Pipeline Components
1. **Niche Evaluator** (`engine1/niche_evaluator.py`):
   - Computes weighted score across AOV, urgency, competition, and search volume.
   - Evaluated 3 candidate niches:
     - **Emergency Tree Removal & Crane Arborists** (Score: **93.5/100**, AOV: \$2,850, Lead Value: \$175) — *SELECTED WINNER*
     - Foundation Repair & Pier Underpinning (Score: 88.0/100)
     - Commercial & Residential Epoxy Flooring (Score: 85.0/100)
   - Seeds schema and persists to SQLite.
2. **Playwright Harvester** (`engine1/scraper.py`):
   - Scrapes real local Google Maps contractors across North Texas (Dallas, Fort Worth, Arlington, Plano, Frisco, Irving, Denton, Garland).
   - Extracts business name, phone number, website, rating, reviews count, address, and municipality.
3. **Gemini 3.8 Flash Enricher** (`engine1/enricher.py`):
   - Generates 2-sentence SEO summaries, structured services arrays, 24/7 emergency dispatch flags, trust badges, price tiers (`$$$` / `$$$$`), and full `Schema.org` JSON-LD specifications.
4. **Static Site Generator** (`engine1/site_generator.py`):
   - Compiles database into `docs/index.html` (interactive two-column UI), `docs/sitemap.xml`, and `docs/robots.txt`.
5. **Master Orchestrator CLI** (`engine1/run_engine1.py`):
   - Unified interface supporting `--all`, `--evaluate`, `--scrape`, `--enrich`, `--build`, `--test`, and `--status`.

---

## CLI Usage

```bash
# Check current database and site status
python3 engine1/run_engine1.py --status

# Run full automated Playwright verification test suite
python3 engine1/run_engine1.py --test

# Execute full end-to-end pipeline (evaluate, harvest, enrich, compile, test)
python3 engine1/run_engine1.py --all
```

---

## 1-Click GitHub Pages Deployment
The generated site resides entirely in `/Users/collincarlton/lean_multimodal_platform/docs/`.
To deploy:
1. Push branch `main` to GitHub (`git push origin main`).
2. In GitHub repository settings:
   - Navigate to **Settings** > **Pages**.
   - Under **Build and deployment**:
     - Source: **Deploy from a branch**
     - Branch: `main` / Folder: `/docs`
   - Click **Save**.
3. The directory will be live instantly at `https://collincarlton.github.io/lean_multimodal_platform/`.
