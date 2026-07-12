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
    def test_event_launcher_kills_complete_process_groups(self) -> None:
        launcher = (ROOT / "harness/start_event.sh").read_text()
        self.assertIn('kill -TERM -- "-$leader"', launcher)
        self.assertIn("set -m", launcher)
        self.assertIn("official-loop-start-20260712-1230", launcher)
        self.assertIn("official Ralph Loop window is 12:30-15:30 KST", launcher)
        self.assertIn("Claude worker requested but Claude Code is not logged in", launcher)

    def test_submission_gate_rejects_identity_and_placeholder_abstract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "paper").mkdir()
            (repo / "paper/main.tex").write_text(
                "\\usepackage[accepted]{icml2026}\n"
                "\\icmltitle{A Placeholder Study of Context Position}\\icmlsetsymbol{x}{x}\n"
                "\\begin{abstract}TODO pending.\\end{abstract}\n"
                "\\label{main-body-end}\n"
                "\\icmlauthor{Matthew Chan}{author}\n"
            )
            gate = ROOT / "harness/gates/check_submission.py"
            result = run(sys.executable, str(gate), cwd=repo)
            self.assertNotEqual(result.returncode, 0)

    def test_submission_gate_accepts_anonymous_title_and_abstract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "paper").mkdir()
            abstract = " ".join(
                [
                    "We study target retrieval under controlled changes in document position and distractor relevance.",
                    "A frozen local language model answers matched questions with deterministic decoding.",
                    "The design separates document length, clause position, distractor quality, and context pruning.",
                    "Paired comparisons support narrow claims about the tested model and synthetic task.",
                    "The resulting artifacts provide a reproducible basis for evaluating context construction choices.",
                ]
            )
            (repo / "paper/main.tex").write_text(
                "\\usepackage{icml2026}\n"
                "\\icmltitle{Where Context Sits Changes Small Model Retrieval}\\icmlsetsymbol{x}{x}\n"
                f"\\begin{{abstract}}{abstract}\\end{{abstract}}\n"
                "\\label{main-body-end}\n"
                "\\icmlauthor{Anonymous Authors}{anon}\n"
            )
            gate = ROOT / "harness/gates/check_submission.py"
            result = run(sys.executable, str(gate), cwd=repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_every_agent_role_uses_event_model_and_high_reasoning(self) -> None:
        loop = (ROOT / "harness/loop.sh").read_text()
        self.assertIn('CODEX_MODEL="${CODEX_MODEL:-gpt-5.6-sol}"', loop)
        self.assertIn('CODEX_REASONING_EFFORT="${CODEX_REASONING_EFFORT:-high}"', loop)
        effort_override = '-c "model_reasoning_effort=\\"$CODEX_REASONING_EFFORT\\""'
        self.assertEqual(loop.count(effort_override), 3)

    def test_claude_worker_is_optional_and_falls_back_to_codex_on_quota(self) -> None:
        loop = (ROOT / "harness/loop.sh").read_text()
        self.assertIn('WORKER_BACKEND="${WORKER_BACKEND:-codex}"', loop)
        self.assertIn('POST_REVIEW_BACKEND="${POST_REVIEW_BACKEND:-$WORKER_BACKEND}"', loop)
        self.assertIn('CLAUDE_MODEL="${CLAUDE_MODEL:-fable}"', loop)
        self.assertIn("--output-format stream-json", loop)
        self.assertIn("retrying this lap with Codex", loop)
        self.assertIn("retrying this lap with Claude", loop)
        self.assertIn("both backends failed consecutively", loop)

    def test_codex_review_quota_falls_back_to_read_only_fable(self) -> None:
        loop = (ROOT / "harness/loop.sh").read_text()
        self.assertIn("run_scientific_review", loop)
        self.assertIn("Codex review limit hit", loop)
        self.assertIn('--permission-mode dontAsk', loop)
        self.assertIn('--tools "Read,Glob,Grep"', loop)

    def test_claude_stream_result_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stream = root / "stream.jsonl"
            output = root / "result.txt"
            stream.write_text(
                '{"type":"assistant","message":{"content":[]}}\n'
                '{"type":"result","result":"Finished the selected task."}\n'
            )
            result = run(
                sys.executable,
                str(ROOT / "harness/extract_claude_result.py"),
                str(stream),
                str(output),
                cwd=root,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(output.read_text(), "Finished the selected task.\n")

    def test_claude_allowed_rate_event_is_not_a_quota_outage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "allowed.jsonl"
            log.write_text(
                '{"type":"rate_limit_event","rate_limit_info":'
                '{"status":"allowed","rateLimitType":"five_hour"}}\n'
                '{"type":"result","is_error":false,"result":"done"}\n'
            )
            result = run(
                sys.executable,
                str(ROOT / "harness/check_quota.py"),
                str(log),
                cwd=root,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_claude_blocked_rate_event_is_a_quota_outage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "blocked.jsonl"
            log.write_text(
                '{"type":"rate_limit_event","rate_limit_info":{"status":"rate_limited"}}\n'
            )
            result = run(
                sys.executable,
                str(ROOT / "harness/check_quota.py"),
                str(log),
                cwd=root,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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

    def test_style_gate_rejects_casual_and_repetitive_paper_voice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "paper").mkdir()
            (repo / "paper/main.tex").write_text(
                "This paper uses a made-up task. "
                "This paper reports the task. "
                "This paper explains the task. "
                "This paper repeats itself.\n"
            )
            result = run(sys.executable, str(ROOT / "harness/gates/check_style.py"), cwd=repo)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("made-up", result.stdout.lower())
            self.assertIn("repeated", result.stdout.lower())

    def test_style_gate_rejects_weak_abstract_rhythm_and_display_bloat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "paper").mkdir()
            (repo / "paper/main.tex").write_text(
                "\\begin{document}\n"
                "\\begin{abstract}Results vary. Position matters. Context hurts.\\end{abstract}\n"
                "Results vary. Position matters. Context hurts.\n"
                + "\\begin{table}x\\end{table}\n" * 5
                + "\\end{document}\n"
            )
            result = run(sys.executable, str(ROOT / "harness/gates/check_style.py"), cwd=repo)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            output = result.stdout.lower()
            self.assertIn("abstract", output)
            self.assertIn("short sentences", output)
            self.assertIn("displays", output)

    def test_style_gate_accepts_concise_professional_paper_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "paper").mkdir()
            (repo / "paper/main.tex").write_text(
                "\\begin{document}\n"
                "\\begin{abstract}\n"
                "We examine whether target position changes retrieval accuracy in synthetic documents. "
                "A frozen language model answers matched questions under deterministic decoding. "
                "Accuracy declines when the target moves behind competing clauses. "
                "The comparison remains limited to one model and one controlled task. "
                "These results motivate testing document structure before expanding context.\n"
                "\\end{abstract}\n"
                "\\section{Results}\n"
                "The paired comparison isolates position while holding each question and competing clause fixed. "
                "Accuracy is lower at later positions, although the estimate remains specific to the tested model.\n"
                "\\begin{table}Selective position estimates.\\end{table}\n"
                "\\begin{figure}Matched scenario summary.\\end{figure}\n"
                "\\end{document}\n"
            )
            result = run(sys.executable, str(ROOT / "harness/gates/check_style.py"), cwd=repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
