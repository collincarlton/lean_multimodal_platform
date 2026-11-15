#!/usr/bin/env python3
"""
Headless Compute Preflight & Job-Spec Adapter for Gemma Quantization.
Fail-closed contract: never fabricates dummy `TFL3` binary payloads and reports
explicit unconfigured status when GCS bucket / remote worker targets are unset.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SYNTHETIC_TFLITE_MARKERS = (
    b"TFL3_LITERT_STAGED_DESCRIPTOR",
    b"TFL3\x00\x00\x00\x00",
)
GCS_BUCKET_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]$")


def assert_home_device(path: Path) -> None:
    home_dev = Path.home().resolve().stat().st_dev
    target = path if path.exists() else path.parent
    if target.exists() and target.stat().st_dev != home_dev:
        raise PermissionError(f"APFS device boundary violation on {path}")


def is_synthetic_tflite(candidate_path: Path | str) -> bool:
    """Detects missing or synthetic stub `.tflite` artifacts (e.g., dummy TFL3 headers)."""
    path = Path(candidate_path)
    if not path.is_file():
        return True
    size = path.stat().st_size
    if size < 4096:
        return True
    with path.open("rb") as f:
        head = f.read(64)
    return any(marker in head for marker in SYNTHETIC_TFLITE_MARKERS)


def preflight_cloud_target(
    gcs_bucket: Optional[str] = None,
    worker_target: Optional[str] = None,
) -> Dict[str, Any]:
    """Validates remote worker and GCS target configuration; fails closed when unset."""
    bucket = (gcs_bucket or os.environ.get("LUNORA_GCS_BUCKET") or "").strip()
    if bucket.startswith("gs://"):
        bucket = bucket[5:].split("/", 1)[0]
    worker = (worker_target or os.environ.get("LUNORA_CLOUD_WORKER_URL") or "").strip()

    missing: List[str] = []
    if not bucket:
        missing.append("gcs_bucket")
    elif not GCS_BUCKET_RE.match(bucket):
        missing.append("gcs_bucket(invalid_format)")
    if not worker:
        missing.append("worker_target")

    configured = len(missing) == 0
    return {
        "status": "PREFLIGHT_READY" if configured else "UNCONFIGURED_FAIL_CLOSED",
        "ready": configured,
        "gcsBucket": bucket or None,
        "workerTarget": worker or None,
        "missingTargets": missing,
        "syntheticBinaryProhibited": True,
        "failClosedReason": (
            None
            if configured
            else f"Missing required remote targets ({', '.join(missing)}); refusing synthetic .tflite generation."
        ),
    }


def build_job_spec(
    model_id: str,
    quant_mode: str,
    output_dir: Path | str,
    gcs_bucket: Optional[str] = None,
    worker_target: Optional[str] = None,
) -> Dict[str, Any]:
    preflight = preflight_cloud_target(gcs_bucket=gcs_bucket, worker_target=worker_target)
    out_path = Path(output_dir)
    target_artifact = out_path / f"gemma_lean_{quant_mode}.tflite"
    return {
        "schemaVersion": "2.0.0",
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "modelId": model_id,
        "quantMode": quant_mode,
        "format": "LiteRT_TFLite",
        "expectedArtifactPath": str(target_artifact),
        "artifactPresentAndValid": not is_synthetic_tflite(target_artifact),
        "targetRuntimes": ["macOS_Desktop", "Chrome_Web"],
        "preflight": preflight,
        "status": preflight["status"],
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail-Closed Cloud Compute Preflight & Gemma Job-Spec Adapter"
    )
    parser.add_argument("--model-id", default="google/gemma-2-2b-it", help="Target model identifier")
    parser.add_argument("--output-dir", default="./exported_models", help="Directory for job-spec & metadata JSON")
    parser.add_argument("--gcs-bucket", default=None, help="Explicit GCS bucket name (or LUNORA_GCS_BUCKET env)")
    parser.add_argument("--worker-target", default=None, help="Explicit remote worker URI (or LUNORA_CLOUD_WORKER_URL env)")
    parser.add_argument("--quant-mode", default="int4", choices=["int4", "int8", "fp16"], help="Quantization scheme")
    parser.add_argument("--spec-only", action="store_true", help="Emit job-spec JSON cleanly without failing exit code")
    return parser.parse_args(argv)


def run_pipeline(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    out_dir = Path(args.output_dir).expanduser().resolve()
    assert_home_device(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    spec = build_job_spec(
        model_id=args.model_id,
        quant_mode=args.quant_mode,
        output_dir=out_dir,
        gcs_bucket=args.gcs_bucket,
        worker_target=args.worker_target,
    )

    spec_file = out_dir / "gemma_job_spec.json"
    meta_file = out_dir / "metadata.json"
    spec_file.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    meta_file.write_text(
        json.dumps(
            {
                "modelId": spec["modelId"],
                "quantMode": spec["quantMode"],
                "format": spec["format"],
                "status": spec["status"],
                "syntheticBinaryProhibited": True,
                "preflight": spec["preflight"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("=== CLOUD COMPUTE PREFLIGHT: GEMMA PIPELINE ===")
    print(json.dumps(spec, indent=2))

    if not spec["preflight"]["ready"] and not args.spec_only:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(run_pipeline())
