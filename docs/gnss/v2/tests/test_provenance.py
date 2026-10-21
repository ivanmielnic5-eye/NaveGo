#!/usr/bin/env python3
"""Unit tests for the standalone retrospective provenance utility."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "eval" / "provenance.py"
spec = importlib.util.spec_from_file_location("navego_provenance", SCRIPT)
prov = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(prov)


def put(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".git").mkdir()
        # The helper tolerates missing Git metadata; a directory named .git is enough
        # to prove paths stay within the isolated test repository.
        self.run = self.root / "docs/gnss/v2/results/v2_test"
        self.run.mkdir(parents=True)
        self.fixes = put(self.root / "docs/gnss/v2/obsgen/fixes/fixes_test.jsonl", b'{"lat":1}\n')
        self.gt = put(self.root / "docs/gnss/v2/gtgen/trajectories/gt_test_1.jsonl", b'{"x":1}\n')
        self.obs = self.root / "docs/gnss/v2/obsgen/fixes/obs_events_test.json"
        self.obs.write_text(json.dumps({"fixes_sha256": hashlib.sha256(self.fixes.read_bytes()).hexdigest(),
                                        "gnss_cfg": {"sigma_m": 1.5}}), encoding="utf-8")
        put(self.root / "docs/gnss/v2/gtgen/events/traj_events_test_1.json", b'{"seed":1}\n')
        for rel in ("docs/gnss/v2/eval/run_all.py", "docs/gnss/v2/eval/metrics.py",
                    "docs/gnss/v2/eval/methods.py", "docs/gnss/v2/eval/provenance.py",
                    "docs/gnss/v2/gtgen/gen_traj.py", "docs/gnss/v2/obsgen/gen_obs.py",
                    "tools/gnss_simulator.py", "docs/gnss/v2/tests/test_recovery.py"):
            put(self.root / rel, b"# test source\n")
        row_base = {
            "fixes_path": str(self.fixes), "gt_path": str(self.gt),
            "obs_events_path": str(self.obs),
            "fix_hash": hashlib.sha256(self.fixes.read_bytes()).hexdigest(),
            "scenario": "S1", "traj": "test", "seed": 1,
            "variant": None, "metrics": {},
        }
        rows = [dict(row_base, method="A"), dict(row_base, method="B")]
        (self.run / "detail.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        (self.run / "by_scenario.csv").write_text("scenario,method\nS1,A\nS1,B\n", encoding="utf-8")
        (self.run / "summary.json").write_text(json.dumps({"phase": "A", "timestamp": "test",
            "n_rows": 2, "n_missing": 0, "criteria": {"C3": {"status": "PASS"}}}), encoding="utf-8")
        self.manifest = self.root / "docs/gnss/v2/provenance_audits/v2_test.manifest.json"

    def tearDown(self):
        self.temp.cleanup()

    def test_create_and_validate_manifest(self):
        data = prov.create_manifest(self.run, self.manifest, self.root)
        self.assertEqual(data["run"]["n_rows_detail"], 2)
        self.assertEqual(len(data["output_artifacts"]), 3)
        self.assertEqual(prov.validate_manifest(self.manifest, self.root), [])

    def test_changed_input_is_detected(self):
        prov.create_manifest(self.run, self.manifest, self.root)
        self.fixes.write_bytes(b'{"lat":2}\n')
        errors = prov.validate_manifest(self.manifest, self.root)
        self.assertTrue(any("SHA-256 no coincide" in e for e in errors), errors)

    def test_changed_output_is_detected(self):
        prov.create_manifest(self.run, self.manifest, self.root)
        (self.run / "summary.json").write_text("{}", encoding="utf-8")
        errors = prov.validate_manifest(self.manifest, self.root)
        self.assertTrue(any("summary.json" in e for e in errors), errors)

    def test_missing_event_hash_is_rejected(self):
        self.obs.write_text(json.dumps({"gnss_cfg": {"sigma_m": 1.5}}), encoding="utf-8")
        with self.assertRaises(prov.ProvenanceError):
            prov.create_manifest(self.run, self.manifest, self.root)

    def test_manifest_never_overwrites_existing_file(self):
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        self.manifest.write_text("keep", encoding="utf-8")
        with self.assertRaises(prov.ProvenanceError):
            prov.create_manifest(self.run, self.manifest, self.root)
        self.assertEqual(self.manifest.read_text(encoding="utf-8"), "keep")

    def test_runtime_capture_manifest_records_start_and_end(self):
        snapshot = prov.capture_runtime_snapshot(
            self.root, run_id="v2_test", phase="A", command=["python", "run_all.py", "--phase", "A"]
        )
        output = self.root / "docs/gnss/v2/results/v2_test/provenance_manifest.json"
        data = prov.create_manifest(self.run, output, self.root, runtime_snapshot=snapshot)
        self.assertEqual(data["audit_mode"], "runtime_capture")
        self.assertEqual(data["historical_code_attribution"]["status"], "captured_at_run_start")
        self.assertTrue(data["run_execution"]["source_files_unchanged_during_run"])
        self.assertEqual(prov.validate_manifest(output, self.root), [])

    def test_runtime_capture_detects_source_change_during_run(self):
        snapshot = prov.capture_runtime_snapshot(
            self.root, run_id="v2_test", phase="A", command=["python", "run_all.py"]
        )
        source = self.root / "docs/gnss/v2/eval/methods.py"
        source.write_text("# changed during simulated run\n", encoding="utf-8")
        output = self.root / "docs/gnss/v2/results/v2_test/provenance_manifest.json"
        prov.create_manifest(self.run, output, self.root, runtime_snapshot=snapshot)
        errors = prov.validate_manifest(output, self.root)
        self.assertTrue(any("fuentes cambiaron" in e for e in errors), errors)

    def test_parity_is_checked_per_scenario_and_seed(self):
        second_fixes = put(self.root / "docs/gnss/v2/obsgen/fixes/fixes_other.jsonl", b'{"lat":3}\n')
        lines = (self.run / "detail.jsonl").read_text(encoding="utf-8").splitlines()
        row = json.loads(lines[1])  # Reemplaza el registro B existente; no crea un duplicado.
        row["fixes_path"] = str(second_fixes)
        row["fix_hash"] = hashlib.sha256(second_fixes.read_bytes()).hexdigest()
        other_obs = self.root / "docs/gnss/v2/obsgen/fixes/obs_events_other.json"
        other_obs.write_text(json.dumps({"fixes_sha256": row["fix_hash"]}), encoding="utf-8")
        row["obs_events_path"] = str(other_obs)
        lines[1] = json.dumps(row)
        (self.run / "detail.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(prov.ProvenanceError, "Paridad de fijaciones fallida"):
            prov.create_manifest(self.run, self.manifest, self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
