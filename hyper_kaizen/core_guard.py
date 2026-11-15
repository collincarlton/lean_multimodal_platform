#!/usr/bin/env python3
"""
Core hardware safety, APFS mount invariants, SQLite WAL governance,
8GB RAM Chromium budget guard, and Zero-Capital GenAI Router.
"""

from __future__ import annotations

import asyncio
import datetime
import gc
import hashlib
import json
import mimetypes
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

HOME_DIR = Path("/Users/collincarlton").resolve()
HOME_DEV = HOME_DIR.stat().st_dev  # Expected 16777223 on APFS volume
SYS_DB_PATH = HOME_DIR / ".lunora_system.db"
ENGINE_DB_PATH = HOME_DIR / "lean_multimodal_platform" / "data" / "engine1.db"
AISTUDIO_SCRIPTS_DIR = HOME_DIR / "AIStudioOrg" / "scripts"
KEYS_PATH = HOME_DIR / ".lunora" / "keys.json"

MODEL_PRIORITY = ["gemini-4-hydrogen", "gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
HTTP_TIMEOUT_MS = 15000
HEAVY_RESOURCE_TYPES = {"image", "media", "font"}


def assert_safe_device(path: Path | str) -> Path:
    """Enforce Virtual Mount Barrier: path (or nearest existing parent) must live on HOME_DEV."""
    p = Path(path).expanduser()
    probe = p
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    if probe.exists():
        dev = os.stat(str(probe)).st_dev
        assert dev == HOME_DEV, f"Virtual Mount Barrier violation on {p}: st_dev={dev} != {HOME_DEV}"
    return p


def get_sqlite_connection(db_path: Path | str = SYS_DB_PATH) -> sqlite3.Connection:
    """Open SQLite connection strictly enforcing LUNORA 5-pragma storage invariant."""
    target = assert_safe_device(db_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    assert_safe_device(target.parent)
    conn = sqlite3.connect(str(target), timeout=15.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA cache_size=-32000;")
    conn.execute("PRAGMA busy_timeout=10000;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.row_factory = sqlite3.Row
    return conn


def init_hyper_kaizen_schema() -> None:
    """Ensure all unified Hyper-Kaizen tables exist inside ~/.lunora_system.db and engine1.db."""
    with get_sqlite_connection(SYS_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS genai_cache (
                prompt_hash TEXT PRIMARY KEY,
                response_json TEXT,
                cached_at TEXT
            )
            """
        )
        # Safely migrate optional column if older table created by cache governor lacks it
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(genai_cache)").fetchall()}
        if "model_used" not in cols:
            conn.execute("ALTER TABLE genai_cache ADD COLUMN model_used TEXT")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gsc_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                niche_slug TEXT NOT NULL,
                url TEXT NOT NULL,
                query TEXT NOT NULL DEFAULT '',
                clicks INTEGER NOT NULL DEFAULT 0,
                impressions INTEGER NOT NULL DEFAULT 0,
                ctr REAL NOT NULL DEFAULT 0.0,
                position REAL NOT NULL DEFAULT 0.0,
                index_status TEXT NOT NULL DEFAULT 'UNKNOWN',
                captured_at TEXT NOT NULL,
                UNIQUE(niche_slug, url, query)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversion_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                niche_slug TEXT NOT NULL,
                page_url TEXT NOT NULL,
                event_type TEXT NOT NULL,
                provider_slug TEXT DEFAULT '',
                metadata_json TEXT DEFAULT '{}',
                timestamp TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS directory_fitness (
                niche_slug TEXT NOT NULL,
                url TEXT NOT NULL,
                fitness_score REAL NOT NULL DEFAULT 0.0,
                clicks_30d INTEGER NOT NULL DEFAULT 0,
                impressions_30d INTEGER NOT NULL DEFAULT 0,
                leads_30d INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                last_mutated_at TEXT DEFAULT '',
                updated_at TEXT NOT NULL,
                PRIMARY KEY (niche_slug, url)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kaizen_mutations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                niche_slug TEXT NOT NULL,
                url TEXT NOT NULL,
                mutation_type TEXT NOT NULL,
                old_val TEXT,
                new_val TEXT,
                reason TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prospect_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                company_slug TEXT UNIQUE NOT NULL,
                website TEXT,
                city TEXT,
                niche TEXT,
                source_directory TEXT DEFAULT '',
                audit_summary TEXT,
                bottlenecks_json TEXT,
                pain_score REAL DEFAULT 0.0,
                icp_score REAL DEFAULT 0.0,
                audit_doc_url TEXT,
                audit_doc_html_path TEXT,
                outreach_status TEXT DEFAULT 'DRAFTED',
                created_at TEXT NOT NULL
            )
            """
        )
        lead_dispatch_sql = """
            CREATE TABLE IF NOT EXISTS lead_dispatch_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                niche_slug TEXT,
                city TEXT,
                lead_summary TEXT,
                recipient_company TEXT,
                recipient_contact TEXT,
                sent_at TEXT,
                status TEXT,
                outcome TEXT
            )
        """
        conn.execute(lead_dispatch_sql)
        conn.commit()
    with get_sqlite_connection(ENGINE_DB_PATH) as econn:
        econn.execute(lead_dispatch_sql)
        econn.commit()


class MemoryBudgetGuard:
    """
    8GB RAM macOS guard for headless Playwright and high-volume refinement.
    Enforces Chromium Semaphore(2), heavy-resource interception, 25-URL context recycling,
    and automatic GC pause when free+inactive memory drops below 900 MB.
    """

    def __init__(
        self,
        max_concurrent_tabs: int = 2,
        recycle_every_n_urls: int = 25,
        min_available_mb: float = 900.0,
    ) -> None:
        self.max_concurrent_tabs = max_concurrent_tabs
        self.recycle_every_n_urls = recycle_every_n_urls
        self.min_available_mb = min_available_mb
        self._semaphore: Optional[asyncio.Semaphore] = None
        self.urls_processed: int = 0
        self.recycle_count: int = 0

    @property
    def semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent_tabs)
        return self._semaphore

    @staticmethod
    def get_memory_stats() -> Dict[str, float]:
        """Inspect host memory via sysctl hw.memsize and vm_stat (no external deps)."""
        total_bytes = 8 * 1024 * 1024 * 1024
        try:
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True, timeout=2.0).strip()
            total_bytes = int(out)
        except Exception:
            pass

        page_size = 4096
        free_pages = 0
        inactive_pages = 0
        speculative_pages = 0
        try:
            vm_out = subprocess.check_output(["vm_stat"], text=True, timeout=2.0)
            m_page = re.search(r"page size of (\d+) bytes", vm_out)
            if m_page:
                page_size = int(m_page.group(1))
            for label, key in [
                (r"Pages free:\s+(\d+)", "free"),
                (r"Pages inactive:\s+(\d+)", "inactive"),
                (r"Pages speculative:\s+(\d+)", "spec"),
            ]:
                m = re.search(label, vm_out)
                if m:
                    val = int(m.group(1))
                    if key == "free":
                        free_pages = val
                    elif key == "inactive":
                        inactive_pages = val
                    else:
                        speculative_pages = val
        except Exception:
            pass

        free_mb = round((free_pages * page_size) / (1024 * 1024), 2)
        available_mb = round(((free_pages + inactive_pages + speculative_pages) * page_size) / (1024 * 1024), 2)
        total_mb = round(total_bytes / (1024 * 1024), 2)
        return {
            "total_mb": total_mb,
            "free_mb": free_mb,
            "available_mb": available_mb,
        }

    def check_memory_pressure(self) -> Tuple[bool, Dict[str, float]]:
        """Return (within_budget, stats); triggers gc.collect() if available < min_available_mb."""
        stats = self.get_memory_stats()
        if stats["available_mb"] > 0 and stats["available_mb"] < self.min_available_mb:
            gc.collect()
            time.sleep(0.75)
            stats = self.get_memory_stats()
        ok = stats["available_mb"] == 0 or stats["available_mb"] >= self.min_available_mb
        return ok, stats

    def note_url_processed(self) -> bool:
        """Increment processed URL counter and return True if browser context should recycle."""
        self.urls_processed += 1
        ok, _ = self.check_memory_pressure()
        if (self.urls_processed % self.recycle_every_n_urls == 0) or not ok:
            self.recycle_count += 1
            gc.collect()
            return True
        return False

    @staticmethod
    async def attach_heavy_abort(page: Any) -> None:
        """Abort images, media, and fonts in Playwright to cut 8GB RAM bandwidth & overhead."""
        async def _abort_heavy(route: Any) -> None:
            try:
                if route.request.resource_type in HEAVY_RESOURCE_TYPES:
                    await route.abort()
                else:
                    await route.continue_()
            except Exception:
                pass

        await page.route("**/*", _abort_heavy)


def _load_governor_helpers() -> Tuple[Any, Callable[[], Optional[str]]]:
    """Import shared TokenBucketGovernor and get_api_key from AIStudioOrg without duplicating logic."""
    if str(AISTUDIO_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(AISTUDIO_SCRIPTS_DIR))
    try:
        from ai_studio_cache_governor import TokenBucketGovernor, get_api_key  # type: ignore

        return TokenBucketGovernor, get_api_key
    except Exception:
        def _fallback_key() -> Optional[str]:
            key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if key:
                return key
            if KEYS_PATH.exists():
                try:
                    data = json.loads(KEYS_PATH.read_text(encoding="utf-8"))
                    return data.get("GEMINI_API_KEY") or data.get("GOOGLE_API_KEY")
                except Exception:
                    return None
            return None

        class _FallbackBucket:
            def acquire(self, tokens: int = 100, wait: bool = False, max_wait: float = 5.0) -> Tuple[bool, float, str]:
                return True, 0.0, "FALLBACK_BUCKET"

        return _FallbackBucket, _fallback_key


def _strip_json_fences(raw: str) -> str:
    txt = raw.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", txt)
    if m:
        return m.group(1).strip()
    return txt


class GenAIRouter:
    """
    Centralized Gemini 3.8 Flash / 2.5 Flash / 2.0 Flash router enforcing:
    - SHA-256 SQLite WAL genai_cache inside ~/.lunora_system.db
    - Shared TokenBucketGovernor (<=15 RPM)
    - http_options={'timeout': 15000} (>=10000ms SDK floor)
    - 5-item batch packing & Two-Pass multimodal/grounded extraction with deterministic fallback
    """

    def __init__(self, models: Optional[List[str]] = None) -> None:
        self.models = models or list(MODEL_PRIORITY)
        gov_cls, key_fn = _load_governor_helpers()
        self.governor = gov_cls()
        self.get_api_key = key_fn
        init_hyper_kaizen_schema()

    @staticmethod
    def pack_batches(items: List[Any], batch_size: int = 5) -> Iterable[List[Any]]:
        for i in range(0, len(items), batch_size):
            yield items[i : i + batch_size]

    @staticmethod
    def _prompt_hash(prompt: str, extra: str = "") -> str:
        return hashlib.sha256((prompt + "||" + extra).encode("utf-8")).hexdigest()

    def _get_cached(self, prompt_hash: str) -> Optional[Dict[str, Any]]:
        with get_sqlite_connection(SYS_DB_PATH) as conn:
            row = conn.execute(
                "SELECT response_json, model_used FROM genai_cache WHERE prompt_hash = ?",
                (prompt_hash,),
            ).fetchone()
            if row and row["response_json"]:
                try:
                    data = json.loads(row["response_json"])
                    if isinstance(data, dict):
                        data.setdefault("_cache_hit", True)
                        if row["model_used"]:
                            data.setdefault("_model", row["model_used"])
                    return data
                except Exception:
                    return None
        return None

    def _set_cache(self, prompt_hash: str, payload: Dict[str, Any], model_used: str) -> None:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with get_sqlite_connection(SYS_DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO genai_cache (prompt_hash, response_json, cached_at, model_used)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(prompt_hash) DO UPDATE SET
                    response_json = excluded.response_json,
                    cached_at = excluded.cached_at,
                    model_used = excluded.model_used
                """,
                (prompt_hash, json.dumps(payload), now_iso, model_used),
            )
            conn.commit()

    def generate_json(
        self,
        prompt: str,
        *,
        image_path: Optional[Path] = None,
        two_pass_evidence: Optional[str] = None,
        fallback_factory: Optional[Callable[[], Dict[str, Any]]] = None,
        est_tokens: int = 1200,
    ) -> Dict[str, Any]:
        """
        Execute JSON-structured Gemini call (or Two-Pass grounded call + image inspection)
        using SHA-256 SQLite cache, 15s timeout floor, model cascade, and deterministic fallback.
        """
        extra_hash = ""
        image_bytes: Optional[bytes] = None
        mime_type = "image/png"
        if image_path is not None:
            img_p = assert_safe_device(image_path)
            if img_p.exists() and img_p.is_file():
                image_bytes = img_p.read_bytes()
                extra_hash += hashlib.sha256(image_bytes).hexdigest()
                guessed, _ = mimetypes.guess_type(str(img_p))
                if guessed:
                    mime_type = guessed
        if two_pass_evidence:
            extra_hash += hashlib.sha256(two_pass_evidence.encode("utf-8")).hexdigest()

        p_hash = self._prompt_hash(prompt, extra_hash)
        cached = self._get_cached(p_hash)
        if cached is not None:
            return cached

        full_prompt = prompt
        if two_pass_evidence:
            full_prompt = (
                f"{prompt}\n\n"
                "PASS-1 VERIFIED EVIDENCE CONTEXT (use ONLY grounded facts from below; return valid JSON):\n"
                f"{two_pass_evidence[:12000]}"
            )

        api_key = self.get_api_key()
        acquired, _, _ = self.governor.acquire(tokens=est_tokens, wait=False)

        if api_key and acquired:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=api_key, http_options={"timeout": HTTP_TIMEOUT_MS})
                contents: Any = full_prompt
                if image_bytes is not None:
                    contents = [
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        full_prompt,
                    ]

                for attempt_idx, model_name in enumerate(self.models):
                    try:
                        resp = client.models.generate_content(
                            model=model_name,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                temperature=0.1,
                                response_mime_type="application/json",
                            ),
                        )
                        raw_text = getattr(resp, "text", None) or ""
                        if raw_text:
                            parsed = json.loads(_strip_json_fences(raw_text))
                            if isinstance(parsed, dict):
                                parsed["_source"] = "gemini_live"
                                parsed["_model"] = model_name
                                self._set_cache(p_hash, parsed, model_name)
                                return parsed
                            if isinstance(parsed, list):
                                wrapped = {"items": parsed, "_source": "gemini_live", "_model": model_name}
                                self._set_cache(p_hash, wrapped, model_name)
                                return wrapped
                    except Exception:
                        if attempt_idx == 0:
                            time.sleep(0.4)
                        continue
            except Exception:
                pass

        # Deterministic offline / quota-safe fallback
        if fallback_factory is not None:
            fb = fallback_factory()
            fb.setdefault("_source", "deterministic_fallback")
            fb.setdefault("_model", "offline-deterministic")
            return fb

        return {"status": "fallback", "_source": "deterministic_fallback", "_model": "offline-deterministic"}
