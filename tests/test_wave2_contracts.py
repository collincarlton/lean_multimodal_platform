import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "genkit_backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class Wave2ContractsTest(unittest.TestCase):
    def test_swift_runner_dedup(self) -> None:
        canonical_dir = REPO_ROOT / "flutter_client" / "macos" / "Runner"
        mirror_dir = REPO_ROOT / "macos" / "Runner"
        for filename in ("FloatingHUDPanel.swift", "AppDelegate.swift"):
            canonical = canonical_dir / filename
            mirror = mirror_dir / filename
            self.assertTrue(canonical.is_file(), f"Missing canonical file: {canonical}")
            self.assertFalse(canonical.is_symlink(), f"Canonical file must not be symlink: {canonical}")
            self.assertTrue(mirror.is_symlink(), f"Mirror should be symlink to canonical: {mirror}")
            self.assertEqual(canonical.resolve(), mirror.resolve())

    def test_flows_security_single_pass_and_models(self) -> None:
        flows_ts = (BACKEND_DIR / "src" / "flows.ts").read_text(encoding="utf-8")
        self.assertNotIn("?key=", flows_ts)
        self.assertIn("'x-goog-api-key': apiKey", flows_ts)
        self.assertNotRegex(flows_ts, re.compile(r"gemini-(1\.5|2\.0|2\.5)-"))
        self.assertEqual(flows_ts.count(":generateContent"), 1)
        self.assertNotIn("pass2Payload", flows_ts)
        self.assertIn("vaultCatalogTool", flows_ts)
        self.assertIn("vaultResolveTool", flows_ts)
        self.assertIn("systemInstruction", flows_ts)
        self.assertIn("STATIC_SYSTEM_INSTRUCTION", flows_ts)
        self.assertIn("responseMimeType: 'application/json'", flows_ts)

    def test_index_routes_cors_and_rpm_contract(self) -> None:
        index_ts = (BACKEND_DIR / "src" / "index.ts").read_text(encoding="utf-8")
        self.assertNotRegex(index_ts, re.compile(r"app\.use\(\s*cors\(\s*\)\s*\)"))
        self.assertIn("LOOPBACK_ORIGIN_RE", index_ts)
        self.assertIn("enforceLoopbackCors", index_ts)
        self.assertIn("enforceRpmLimit", index_ts)
        self.assertIn("app.get('/healthz'", index_ts)
        self.assertIn("app.get('/api/health'", index_ts)
        self.assertIn("app.post('/api/reason', enforceRpmLimit", index_ts)
        self.assertIn("app.post('/gateway/stream', enforceRpmLimit", index_ts)
        self.assertIn("text/event-stream", index_ts)
        self.assertIn("data: [DONE]", index_ts)

    def test_dist_runtime_limiter_and_helpers(self) -> None:
        dist_limiter = BACKEND_DIR / "dist" / "rate_limiter.js"
        dist_flows = BACKEND_DIR / "dist" / "flows.js"
        self.assertTrue(dist_limiter.is_file(), "Build genkit_backend before running contract tests")
        self.assertTrue(dist_flows.is_file(), "Build genkit_backend before running contract tests")

        node_script = """
const assert = require('assert');
const { SlidingWindowRpmLimiter } = require('./dist/rate_limiter');
const { getModelPriority, normalizeRawInput } = require('./dist/flows');

let now = 1000000;
const limiter = new SlidingWindowRpmLimiter(99, 60000, () => now);
for (let i = 0; i < 15; i += 1) {
  const res = limiter.tryAcquire();
  assert.strictEqual(res.allowed, true);
  assert.strictEqual(res.limit, 15);
  assert.strictEqual(res.remaining, 14 - i);
}
const blocked = limiter.tryAcquire();
assert.strictEqual(blocked.allowed, false);
assert.strictEqual(blocked.remaining, 0);
assert.ok(blocked.retryAfterSeconds >= 1);

now += 60001;
const recovered = limiter.tryAcquire();
assert.strictEqual(recovered.allowed, true);
assert.strictEqual(recovered.remaining, 14);

const retiredFallback = getModelPriority('gemini-2.0-flash');
assert.strictEqual(retiredFallback[0], 'gemini-3.5-flash');
assert.ok(retiredFallback.includes('gemini-3.5-flash-lite'));

const validOverride = getModelPriority('gemini-3-flash-preview');
assert.strictEqual(validOverride[0], 'gemini-3-flash-preview');
assert.strictEqual(validOverride[1], 'gemini-3.5-flash');

const normalized = normalizeRawInput({
  prompt: 'Inspect rotor',
  audio_b64: 'AAAA',
  image_b64: 'BBBB',
  context: { rpm: 1200 },
});
assert.strictEqual(normalized.audioBase64, 'AAAA');
assert.strictEqual(normalized.imageBase64, 'BBBB');
assert.ok(normalized.prompt.includes('[GATEWAY CONTEXT]'));
assert.ok(normalized.prompt.includes('1200'));
console.log(JSON.stringify({ ok: true, modelTop: validOverride[0] }));
"""
        proc = subprocess.run(
            ["node", "-e", node_script],
            cwd=str(BACKEND_DIR),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, f"stderr={proc.stderr} stdout={proc.stdout}")
        data = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertTrue(data["ok"])

    def test_engine1_scraper_seed_gating(self) -> None:
        import asyncio
        from engine1 import scraper

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_engine1.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                """
                CREATE TABLE listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    niche_id INTEGER NOT NULL,
                    business_name TEXT NOT NULL,
                    phone TEXT,
                    website TEXT,
                    rating REAL,
                    reviews_count INTEGER,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    is_verified INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT,
                    UNIQUE(niche_id, business_name, phone)
                );
                """
            )
            conn.commit()
            conn.close()

            orig_db_path = scraper.DB_PATH
            scraper.DB_PATH = db_path
            try:
                inserted = asyncio.run(
                    scraper.persist_listings(
                        1,
                        [
                            {
                                "business_name": "Verified Live Tree Care",
                                "phone": "(214) 555-0199",
                                "website": "https://example.org",
                                "rating": 4.9,
                                "reviews_count": 42,
                                "address": "100 Main St, Dallas, TX",
                                "city": "Dallas",
                                "state": "TX",
                                "zip_code": "75201",
                                "is_verified": 1,
                            },
                            {
                                "business_name": "Seed Demo Prospect",
                                "phone": "(972) 555-0100",
                                "website": "N/A",
                                "rating": 4.5,
                                "reviews_count": 10,
                                "address": "200 Oak St, Plano, TX",
                                "city": "Plano",
                                "state": "TX",
                                "zip_code": "75024",
                                "is_verified": 0,
                            },
                        ],
                    )
                )
                self.assertEqual(inserted, 2)
                conn = sqlite3.connect(str(db_path))
                rows = dict(
                    conn.execute(
                        "SELECT business_name, is_verified FROM listings"
                    ).fetchall()
                )
                conn.close()
                self.assertEqual(rows["Verified Live Tree Care"], 1)
                self.assertEqual(rows["Seed Demo Prospect"], 0)
            finally:
                scraper.DB_PATH = orig_db_path


if __name__ == "__main__":
    unittest.main()
