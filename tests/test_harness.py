#!/usr/bin/env python3
"""Regression tests for event-critical harness invariants."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(
    *args: str,
    cwd: Path,
    check: bool = False,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Harness Test",
        "GIT_AUTHOR_EMAIL": "harness@example.invalid",
        "GIT_COMMITTER_NAME": "Harness Test",
        "GIT_COMMITTER_EMAIL": "harness@example.invalid",
        **(env_extra or {}),
    }
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, check=check)


class HarnessRegressionTests(unittest.TestCase):
    def test_review_waits_for_green_paper_then_fires_immediately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "paper").mkdir()
            (repo / "reviews").mkdir()
            (repo / "paper/main.pdf").write_bytes(b"pdf")
            (repo / "results.json").write_text("{}\n")
            (repo / "VERIFY.log").write_text(
                "--- gates @ iteration 3 12:00:00 ---\n"
                "FAIL  results-sane\n"
                "gates failed: 1\n"
            )
            due = ROOT / "harness/review_due.sh"
            red = run("bash", str(due), "3", cwd=repo)
            self.assertNotEqual(red.returncode, 0)

            (repo / "VERIFY.log").write_text(
                "--- gates @ iteration 4 12:05:00 ---\n"
                "PASS  results-sane\n"
                "gates failed: 0\n"
            )
            first_green = run("bash", str(due), "4", cwd=repo)
            self.assertEqual(first_green.returncode, 0, first_green.stdout + first_green.stderr)

            (repo / "reviews/iter-4.md").write_text("review\n")
            not_cadence = run("bash", str(due), "5", cwd=repo)
            self.assertNotEqual(not_cadence.returncode, 0)
            too_soon = run("bash", str(due), "6", cwd=repo)
            self.assertNotEqual(too_soon.returncode, 0)
            cadence = run("bash", str(due), "7", cwd=repo)
            self.assertEqual(cadence.returncode, 0, cadence.stdout + cadence.stderr)

    def test_checkpoint_tags_the_tree_that_just_passed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "harness").mkdir()
            (repo / "reviews").mkdir()
            (repo / "paper").mkdir()
            shutil.copy2(ROOT / "harness/checkpoint.sh", repo / "harness/checkpoint.sh")
            shutil.copy2(ROOT / "harness/ratchet.sh", repo / "harness/ratchet.sh")
            run("git", "init", "-q", cwd=repo, check=True)

            (repo / "paper/main.tex").write_text("old paper\n")
            (repo / "VERIFY.log").write_text("seed\n")
            run("git", "add", "-A", cwd=repo, check=True)
            run("git", "commit", "-qm", "seed", cwd=repo, check=True)

            (repo / "paper/main.tex").write_text("newly gated paper\n")
            (repo / "VERIFY.log").write_text(
                "--- gates @ iteration 3 12:00:00 ---\n"
                "PASS  frozen-inputs\n"
                "PASS  citations-resolve\n"
                "PASS  no-number-literals\n"
                "PASS  pipeline-fresh\n"
                "PASS  results-sane\n"
                "PASS  prose-style\n"
                "PASS  latex-compiles\n"
                "gates failed: 0\n"
            )
            (repo / "reviews/iter-3.md").write_text(
                '{"overall": 3, "rubric": 6, "recommendation": "reject"}\n'
            )

            result = run("bash", "harness/checkpoint.sh", "3", cwd=repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            tag = run("git", "tag", "-l", "paper-v*", cwd=repo, check=True).stdout.strip()
            self.assertTrue(tag)
            tagged = run("git", "show", f"{tag}^{{}}:paper/main.tex", cwd=repo, check=True).stdout
            self.assertEqual(tagged, "newly gated paper\n")
            head = run("git", "rev-parse", "HEAD", cwd=repo, check=True).stdout.strip()
            target = run("git", "rev-parse", f"{tag}^{{}}", cwd=repo, check=True).stdout.strip()
            self.assertEqual(target, head)
            promoted = run(
                "bash",
                "harness/ratchet.sh",
                "3",
                cwd=repo,
                env_extra={"RATCHET_PAPER_ONLY": "1"},
            )
            self.assertEqual(promoted.returncode, 0, promoted.stdout + promoted.stderr)
            green_tags = run("git", "tag", "-l", "green-v*", cwd=repo, check=True).stdout.splitlines()
            self.assertEqual(len(green_tags), 1)

    def test_number_gate_rejects_small_hand_typed_integer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "paper").mkdir()
            (repo / "paper/main.tex").write_text("The model answered 19 cases correctly.\n")
            result = run(sys.executable, str(ROOT / "harness/gates/check_numbers.py"), cwd=repo)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sanity_gate_rejects_unknown_units_and_fake_script_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "results.json").write_text(
                json.dumps(
                    {
                        "meta": {"generated_by": "analysis/run_all.py"},
                        "values": {
                            "sampleSize": {
                                "value": 100,
                                "unit": "count",
                                "desc": "sample",
                                "script": "analysis/does_not_exist.py",
                            },
                            "mystery": {
                                "value": 1,
                                "unit": "bananas",
                                "desc": "invalid unit",
                                "script": "analysis/does_not_exist.py",
                            },
                        },
                    }
                )
            )
            result = run(sys.executable, str(ROOT / "harness/gates/check_sanity.py"), cwd=repo)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_frozen_input_gate_detects_model_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            model_dir = repo / "data/models"
            data_dir = repo / "data/cache/nlsy97"
            model_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            model = model_dir / "model.gguf"
            dataset = data_dir / "data.csv"
            model.write_bytes(b"frozen model")
            dataset.write_bytes(b"frozen data")
            (model_dir / "CHECKSUMS.txt").write_text(
                f"{hashlib.sha256(model.read_bytes()).hexdigest()}  {model.name}\n"
            )
            (data_dir / "CHECKSUMS.txt").write_text(
                f"{hashlib.sha256(dataset.read_bytes()).hexdigest()}  {dataset.name}\n"
            )
            gate = ROOT / "harness/gates/check_frozen.sh"
            clean = run("bash", str(gate), cwd=repo)
            self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
            model.write_bytes(b"tampered model")
            tampered = run("bash", str(gate), cwd=repo)
            self.assertNotEqual(tampered.returncode, 0, tampered.stdout + tampered.stderr)

    def test_pdf_gate_rejects_suppressed_running_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "paper").mkdir()
            (repo / "paper/main.tex").write_text("placeholder\n")
            bindir = repo / "bin"
            bindir.mkdir()
            commands = {
                "tectonic": "#!/bin/sh\ntouch paper/main.pdf\n",
                "pdftotext": (
                    "#!/bin/sh\nprintf '%s\\n' 'Title Suppressed Due to Excessive Size' > \"$2\"\n"
                ),
                "pdfinfo": "#!/bin/sh\nprintf '%s\\n' 'Pages: 4'\n",
            }
            for name, source in commands.items():
                path = bindir / name
                path.write_text(source)
                path.chmod(0o755)
            result = run(
                "bash",
                str(ROOT / "harness/gates/check_pdf.sh"),
                cwd=repo,
                env_extra={"PATH": f"{bindir}:{os.environ['PATH']}"},
            )
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("suppressed", (result.stdout + result.stderr).lower())


if __name__ == "__main__":
    unittest.main()
