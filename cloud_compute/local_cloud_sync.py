#!/usr/bin/env python3
"""
Cloud Model Preflight & Knowledge Vault Sync Adapter.
Fail-closed: never writes dummy `TFL3` binary stubs and reports explicit
unconfigured status when GCS/remote worker targets are unset.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from gemma_pipeline_runner import is_synthetic_tflite, preflight_cloud_target

PROJECT_ROOT = SCRIPT_DIR.parent
VAULT_MANIFEST = PROJECT_ROOT / "knowledge_vault" / "manifest.json"
ASSETS_DIR = PROJECT_ROOT / "assets" / "models"


def audit_host_ram() -> float:
    print("=== 1. LOCAL HOST RESOURCE ENFORCEMENT ===")
    try:
        res = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
        ram_gb = int(res) / (1024**3)
    except Exception:
        ram_gb = 8.0
    print(f"Host RAM: {ram_gb:.1f} GB (iMac 2019)")
    if ram_gb <= 8.5:
        print(
            "[GUARD ACTIVE] Lean Local Rule Enforced: Local model training and unquantized inference are STRICTLY PROHIBITED."
        )
    return ram_gb


def check_gcloud_storage_status(gcs_bucket: Optional[str] = None) -> Dict[str, Any]:
    gcloud_bin = shutil.which("gcloud")
    project: Optional[str] = None
    if gcloud_bin:
        try:
            project = (
                subprocess.check_output(
                    [gcloud_bin, "config", "get-value", "project"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=4,
                ).strip()
                or None
            )
        except Exception:
            project = None

    bucket = (gcs_bucket or os.environ.get("LUNORA_GCS_BUCKET") or "").strip() or None
    return {
        "gcloudAvailable": gcloud_bin is not None,
        "gcpProject": project,
        "gcsBucketConfigured": bucket is not None,
        "gcsBucket": bucket,
    }


def sync_model_metadata(
    manifest_path: Path = VAULT_MANIFEST,
    assets_dir: Path = ASSETS_DIR,
    gcs_bucket: Optional[str] = None,
    worker_target: Optional[str] = None,
) -> Dict[str, Any]:
    print("=== 2. KNOWLEDGE VAULT PREFLIGHT SYNCHRONIZATION ===")
    assets_dir.mkdir(parents=True, exist_ok=True)
    preflight = preflight_cloud_target(gcs_bucket=gcs_bucket, worker_target=worker_target)
    gcloud_info = check_gcloud_storage_status(gcs_bucket=gcs_bucket)

    staged_file = assets_dir / "gemma_lean_int4.tflite"
    purged_stub = False
    if staged_file.exists() and is_synthetic_tflite(staged_file):
        staged_file.unlink()
        purged_stub = True

    preflight_descriptor_path = assets_dir / "gemma_lean_int4.preflight.json"
    descriptor = {
        "id": "TFLITE-GEMMA-INT4",
        "status": preflight["status"],
        "ready": preflight["ready"],
        "purgedSyntheticStub": purged_stub,
        "syntheticBinaryProhibited": True,
        "preflight": preflight,
        "gcloud": gcloud_info,
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    preflight_descriptor_path.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")

    manifest_data: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest_data = {}

    sources = manifest_data.get("indexedSources", [])
    bucket_uri = (
        f"gs://{preflight['gcsBucket']}/models/gemma_lean_int4.tflite"
        if preflight["gcsBucket"]
        else "UNCONFIGURED"
    )
    model_entry = {
        "id": "TFLITE-GEMMA-INT4",
        "type": "QUANTIZED_MODEL_PREFLIGHT",
        "title": "Gemma 2 2B Domain Adapted (LiteRT INT4 Quantized)",
        "uri": bucket_uri,
        "status": preflight["status"],
        "preflightManifest": str(preflight_descriptor_path.relative_to(PROJECT_ROOT))
        if preflight_descriptor_path.is_relative_to(PROJECT_ROOT)
        else str(preflight_descriptor_path),
        "quantScheme": "dynamic_int4",
        "maxRamBudgetMb": 512,
        "syntheticBinaryProhibited": True,
    }

    sources = [s for s in sources if s.get("id") != model_entry["id"]]
    sources.append(model_entry)
    manifest_data["indexedSources"] = sources
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

    print(f"Updated manifest preflight entry: {model_entry['id']} -> {preflight['status']}")
    return descriptor


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-Closed Cloud Model Preflight Sync")
    parser.add_argument("--gcs-bucket", default=None, help="Explicit GCS bucket name (or LUNORA_GCS_BUCKET env)")
    parser.add_argument("--worker-target", default=None, help="Explicit remote worker URI (or LUNORA_CLOUD_WORKER_URL env)")
    parser.add_argument("--status", action="store_true", help="Report preflight status cleanly (exit 0)")
    args = parser.parse_args(argv)

    audit_host_ram()
    descriptor = sync_model_metadata(gcs_bucket=args.gcs_bucket, worker_target=args.worker_target)
    print("=== 3. GOOGLE CLOUD STORAGE PREFLIGHT ===")
    print(json.dumps(descriptor, indent=2))

    if not descriptor["ready"] and not args.status:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
