import base64
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AISTUDIO_SCRIPTS = Path("/Users/collincarlton/AIStudioOrg/scripts")

for path_entry in (str(REPO_ROOT), str(AISTUDIO_SCRIPTS)):
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)


class Wave3ContractsTest(unittest.TestCase):
    def test_gemma_pipeline_runner_fail_closed_no_dummy_binary(self) -> None:
        from cloud_compute import gemma_pipeline_runner as runner

        prev_bucket = os.environ.pop("LUNORA_GCS_BUCKET", None)
        prev_worker = os.environ.pop("LUNORA_CLOUD_WORKER_URL", None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                out_dir = Path(tmpdir) / "exported"
                rc = runner.run_pipeline(["--output-dir", str(out_dir)])
                self.assertEqual(rc, 2)
                self.assertFalse((out_dir / "gemma_lean_int4.tflite").exists())

                spec = json.loads((out_dir / "gemma_job_spec.json").read_text(encoding="utf-8"))
                self.assertEqual(spec["status"], "UNCONFIGURED_FAIL_CLOSED")
                self.assertFalse(spec["preflight"]["ready"])
                self.assertTrue(spec["preflight"]["syntheticBinaryProhibited"])
                self.assertIn("gcs_bucket", spec["preflight"]["missingTargets"])
                self.assertIn("worker_target", spec["preflight"]["missingTargets"])

                ready_preflight = runner.preflight_cloud_target(
                    gcs_bucket="gs://valid-test-bucket",
                    worker_target="https://worker.internal.invalid/run",
                )
                self.assertTrue(ready_preflight["ready"])
                self.assertEqual(ready_preflight["status"], "PREFLIGHT_READY")
        finally:
            if prev_bucket is not None:
                os.environ["LUNORA_GCS_BUCKET"] = prev_bucket
            if prev_worker is not None:
                os.environ["LUNORA_CLOUD_WORKER_URL"] = prev_worker

    def test_local_cloud_sync_purges_synthetic_stub(self) -> None:
        from cloud_compute import gemma_pipeline_runner as runner
        from cloud_compute import local_cloud_sync as sync_mod

        prev_bucket = os.environ.pop("LUNORA_GCS_BUCKET", None)
        prev_worker = os.environ.pop("LUNORA_CLOUD_WORKER_URL", None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_root = Path(tmpdir)
                manifest_path = tmp_root / "manifest.json"
                assets_dir = tmp_root / "assets"
                assets_dir.mkdir(parents=True, exist_ok=True)
                stub_file = assets_dir / "gemma_lean_int4.tflite"
                stub_file.write_bytes(b"TFL3_LITERT_STAGED_DESCRIPTOR")
                self.assertTrue(runner.is_synthetic_tflite(stub_file))

                descriptor = sync_mod.sync_model_metadata(
                    manifest_path=manifest_path,
                    assets_dir=assets_dir,
                )
                self.assertEqual(descriptor["status"], "UNCONFIGURED_FAIL_CLOSED")
                self.assertTrue(descriptor["purgedSyntheticStub"])
                self.assertFalse(stub_file.exists())
                self.assertTrue((assets_dir / "gemma_lean_int4.preflight.json").is_file())

                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                entry = manifest["indexedSources"][0]
                self.assertEqual(entry["status"], "UNCONFIGURED_FAIL_CLOSED")
                self.assertEqual(entry["uri"], "UNCONFIGURED")
        finally:
            if prev_bucket is not None:
                os.environ["LUNORA_GCS_BUCKET"] = prev_bucket
            if prev_worker is not None:
                os.environ["LUNORA_CLOUD_WORKER_URL"] = prev_worker

    def test_gemini_live_bridge_relay_contracts(self) -> None:
        import gemini_live_bridge as glb

        self.assertEqual(glb.assert_loopback_host("127.0.0.1"), "127.0.0.1")
        with self.assertRaises(ValueError):
            glb.assert_loopback_host("0.0.0.0")
        with self.assertRaises(ValueError):
            glb.assert_loopback_host("192.168.1.50")

        self.assertNotIn("?key=", glb.GEMINI_LIVE_WS_URL)
        self.assertIn("gemini-3.8-live", glb.LIVE_RELAY_MODELS)
        self.assertIn("gemini-3.1-flash-live-preview", glb.LIVE_RELAY_MODELS)

        pipeline = glb.CoreAudioPipeline()
        pcm = pipeline.generate_synthetic_tone(frequency=440.0, duration_seconds=0.1)
        wav_hdr = (
            b"RIFF"
            + struct.pack("<I", 36 + len(pcm))
            + b"WAVEfmt "
            + struct.pack(
                "<IHHIIHH",
                16,
                1,
                glb.CHANNELS,
                glb.SAMPLE_RATE,
                glb.SAMPLE_RATE * glb.SAMPLE_WIDTH,
                glb.SAMPLE_WIDTH,
                16,
            )
            + b"data"
            + struct.pack("<I", len(pcm))
        )
        wav_b64 = base64.b64encode(wav_hdr + pcm).decode("utf-8")
        pkt, local = glb.translate_client_frame(
            json.dumps({"audio_b64": wav_b64, "mimeType": "audio/wav"}),
            pipeline,
        )
        self.assertIsNone(local)
        self.assertIsNotNone(pkt)
        chunk = pkt["realtime_input"]["media_chunks"][0]
        self.assertEqual(chunk["mime_type"], "audio/pcm;rate=16000")
        self.assertEqual(base64.b64decode(chunk["data"]), pcm)

        # Stdio relay smoke check with ping frame (offline, zero API spend)
        proc = subprocess.run(
            ["/usr/local/bin/python3", str(AISTUDIO_SCRIPTS / "gemini_live_bridge.py"), "--stdio-relay"],
            input='{"type":"ping"}\n',
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        reply = json.loads(proc.stdout.strip())
        self.assertEqual(reply["type"], "pong")


if __name__ == "__main__":
    unittest.main()
