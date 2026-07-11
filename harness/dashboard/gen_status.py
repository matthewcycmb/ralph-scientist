#!/usr/bin/env python3
"""Generate logs/status.json for the live dashboard. Strictly a read-only
observer — it never writes anything the loop or agents read."""
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sh(*args):
    try:
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def tail(path, n=40):
    p = ROOT / path
    if not p.exists():
        return ""
    return "\n".join(p.read_text(errors="replace").splitlines()[-n:])


def last_gate_block():
    p = ROOT / "VERIFY.log"
    txt = p.read_text(errors="replace") if p.exists() else ""
    blocks = re.split(r"(?=--- gates @ iteration )", txt)
    last = blocks[-1] if blocks else ""
    gates = re.findall(r"^(PASS|FAIL)\s+(\S+)", last, re.M)
    m = re.search(r"iteration (\d+) (\d\d:\d\d:\d\d)", last)
    return {
        "iter": m.group(1) if m else "?",
        "time": m.group(2) if m else "",
        "gates": [{"name": name, "ok": st == "PASS"} for st, name in gates],
    }


def run_cutoff():
    """Start-of-current-run boundary: everything older is a previous run's state.
    logs/iter-1.log is rewritten when a run's first lap begins."""
    f = ROOT / "logs" / "iter-1.log"
    return f.stat().st_mtime - 90 if f.exists() else 0


def parse_verdict(path):
    found = re.findall(r'\{"overall".*?\}', path.read_text(errors="replace"))
    if not found:
        return None
    try:
        return json.loads(found[-1])
    except json.JSONDecodeError:
        return None


LEDGER_RE = re.compile(r"^LEDGER:\s*(new|persisting|resolved)\s*\|\s*([a-z0-9][a-z0-9-]*)\s*\|\s*(.*)$", re.M | re.I)


def parse_ledger(path):
    """Reviewer's criticism ledger -> per-review counts + the oldest open item."""
    items = []
    for status_, slug, rest in LEDGER_RE.findall(path.read_text(errors="replace")):
        it = {"status": status_.lower(), "slug": slug}
        m = re.search(r"since=iter-(\d+)", rest)
        if m:
            it["since"] = int(m.group(1))
        items.append(it)
    if not items:
        return None
    open_items = [i for i in items if i["status"] == "persisting"]
    oldest = min(open_items, key=lambda i: i.get("since", 10**6), default=None)
    return {
        "new": sum(1 for i in items if i["status"] == "new"),
        "persisting": len(open_items),
        "resolved": sum(1 for i in items if i["status"] == "resolved"),
        "resolved_slugs": [i["slug"] for i in items if i["status"] == "resolved"],
        "oldest": (oldest["slug"] + (f" (since lap {oldest['since']})" if "since" in oldest else "")) if oldest else None,
    }


def reviews():
    out = []
    rdir = ROOT / "reviews"
    if not rdir.is_dir():
        return out
    cutoff = run_cutoff()
    fixed_slugs = set()  # cumulative UNIQUE fixes — a reviewer re-listing an old win can't inflate this
    for f in sorted(rdir.glob("iter-*.md"), key=lambda p: int(re.search(r"\d+", p.name).group())):
        if f.stat().st_mtime < cutoff:
            continue  # previous run's review
        j = parse_verdict(f)
        if j:
            n = int(re.search(r"\d+", f.name).group())
            j["iter"] = n
            led = parse_ledger(f)
            if led:
                fixed_slugs.update(led.pop("resolved_slugs"))
                led["cum_fixed"] = len(fixed_slugs)
                j["ledger"] = led
            confirm = rdir / f"confirm-{n}.md"
            if confirm.exists():
                cj = parse_verdict(confirm)
                if cj:
                    j["confirm"] = cj.get("rubric", cj.get("overall"))
            out.append(j)
    return out


def newest_agent_msg():
    msgs = sorted((ROOT / "logs").glob("*-msg-*.txt"), key=lambda p: p.stat().st_mtime) if (ROOT / "logs").is_dir() else []
    if not msgs:
        return {"file": "", "text": ""}
    return {"file": msgs[-1].name, "text": msgs[-1].read_text(errors="replace")[-1500:]}


def tokens_per_lap():
    out = []
    ldir = ROOT / "logs"
    if not ldir.is_dir():
        return out
    for f in sorted(ldir.glob("iter-*.log"), key=lambda p: int(re.search(r"\d+", p.name).group())):
        m = re.search(r"tokens used\n([\d,]+)", f.read_text(errors="replace"))
        out.append({"iter": int(re.search(r"\d+", f.name).group()), "tokens": m.group(1) if m else None})
    return out


def paper_stats():
    pdf = ROOT / "paper" / "main.pdf"
    tex = ROOT / "paper" / "main.tex"
    res = ROOT / "results.json"
    words = len(tex.read_text(errors="replace").split()) if tex.exists() else 0
    nvals = 0
    if res.exists():
        try:
            nvals = len(json.loads(res.read_text()).get("values", {}))
        except json.JSONDecodeError:
            pass
    return {
        "pdf_exists": pdf.exists(),
        "pdf_mtime": int(pdf.stat().st_mtime) if pdf.exists() else 0,
        "pdf_kb": round(pdf.stat().st_size / 1024) if pdf.exists() else 0,
        "tex_words": words,
        "values": nvals,
    }


def paper_tag_by_iter():
    """Map lap number -> paper-vN, from the iter= recorded in each tag message."""
    raw = sh("git", "tag", "-l", "paper-v*", "--merged", "HEAD", "--format=%(refname:short)|%(contents:subject)")
    out = {}
    for line in raw.splitlines():
        if "|" in line:
            name, msg = line.split("|", 1)
            m = re.search(r"iter=(\d+)", msg)
            if m and int(m.group(1)) not in out:
                out[int(m.group(1))] = name
    return out


def drafts():
    out = []
    ddir = ROOT / "drafts"
    if not ddir.is_dir():
        return out
    cutoff = run_cutoff()
    tags = paper_tag_by_iter()
    for f in sorted(ddir.glob("iter-*.pdf"), key=lambda p: int(re.search(r"\d+", p.name).group())):
        if f.stat().st_mtime < cutoff:
            continue  # previous run's draft
        n = int(re.search(r"\d+", f.name).group())
        out.append({"iter": n,
                    "kb": round(f.stat().st_size / 1024),
                    "path": f"/drafts/{f.name}",
                    "tag": tags.get(n)})
    return out


def gate_history():
    p = ROOT / "VERIFY.log"
    txt = p.read_text(errors="replace") if p.exists() else ""
    out = []
    for block in re.split(r"(?=--- gates @ iteration )", txt):
        m = re.search(r"iteration (\d+) (\d\d:\d\d:\d\d)", block)
        f = re.search(r"gates failed: (\d+)", block)
        if m and f:
            out.append({"iter": int(m.group(1)), "time": m.group(2)[:5], "fails": int(f.group(1))})
    # show only the CURRENT run: slice from the most recent "iteration 1"
    for i in range(len(out) - 1, -1, -1):
        if out[i]["iter"] == 1:
            out = out[i:]
            break
    return out[-40:]


def paper_log():
    since = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(run_cutoff())) if run_cutoff() else "1970-01-01"
    raw = sh("git", "log", "-14", f"--since={since}", "--date=format:%H:%M", "--pretty=@%h|%ad|%s",
             "--numstat", "--", "paper/main.tex", "paper/refs.bib")
    entries, cur = [], None
    for line in raw.splitlines():
        if line.startswith("@"):
            h, t, s = line[1:].split("|", 2)
            cur = {"hash": h, "time": t, "subject": s, "add": 0, "rm": 0, "msg": ""}
            entries.append(cur)
        elif cur and "\t" in line:
            parts = line.split("\t")
            if len(parts) == 3 and parts[0].isdigit():
                cur["add"] += int(parts[0])
                cur["rm"] += int(parts[1]) if parts[1].isdigit() else 0
    # agent laps only — harness/dashboard commits are not paper work
    entries = [e for e in entries if (e["add"] or e["rm"]) and re.match(r"loop: iteration \d+", e["subject"])]
    tags = paper_tag_by_iter()
    for e in entries:
        n = int(re.match(r"loop: iteration (\d+)", e["subject"]).group(1))
        e["lap"] = n
        e["tag"] = tags.get(n)
        msg = ROOT / "logs" / f"last-msg-{n}.txt"
        if msg.exists():
            text = " ".join(msg.read_text(errors="replace").split())
            e["msg"] = text[:420] + ("…" if len(text) > 420 else "")
    return entries


def total_tokens():
    total = 0
    for t in tokens_per_lap():
        if t["tokens"]:
            total += int(t["tokens"].replace(",", ""))
    return total


def run_elapsed():
    pid = sh("pgrep", "-f", "harness/loop.sh").split("\n")[0].strip()
    if not pid:
        return None
    et = sh("ps", "-o", "etime=", "-p", pid).strip()
    if not et:
        return None
    days = 0
    if "-" in et:
        d, et = et.split("-")
        days = int(d)
    parts = [int(x) for x in et.split(":")]
    while len(parts) < 3:
        parts = [0] + parts
    return days * 86400 + parts[0] * 3600 + parts[1] * 60 + parts[2]


def current_lap():
    """Current lap = last inspected lap + 1. Its start time = the commit that
    closed the previous lap (file timestamps lie across runs; git doesn't)."""
    gh = gate_history()
    raw = sh("git", "log", "-1", "--grep", "^loop: iteration", "--format=%ct|%s")
    if gh:
        prev = gh[-1]["iter"]
        started = 0
        if raw and "|" in raw:
            ts, subj = raw.split("|", 1)
            m = re.search(r"iteration (\d+)", subj)
            if m and int(m.group(1)) == prev:
                started = int(ts)
        return {"n": prev + 1, "started": started}
    el = run_elapsed()
    if el is not None:
        return {"n": 1, "started": int(time.time()) - el}
    return {"n": None, "started": 0}


def last_activity():
    ldir = ROOT / "logs"
    if not ldir.is_dir():
        return 0
    times = [f.stat().st_mtime for f in ldir.glob("*.log")]
    return int(max(times)) if times else 0


def readability():
    """Flesch reading ease of the paper's prose — the humanizer's scoreboard.
    Deterministic, computed from main.tex with LaTeX stripped; no model call.
    Rough anchors: 30 = academic dense, 50 = quality newspaper, 60+ = plain."""
    p = ROOT / "paper" / "main.tex"
    if not p.exists():
        return None
    txt = p.read_text(errors="replace")
    txt = re.sub(r"(?<!\\)%.*", "", txt)
    txt = re.sub(r"\$[^$]*\$", " ", txt)
    txt = re.sub(r"\\begin\{(table|tabular|figure|equation|abstract)\*?\}", " ", txt)
    txt = re.sub(r"\\end\{[a-z]+\*?\}", " ", txt)
    txt = re.sub(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?", " ", txt)
    txt = re.sub(r"[{}~]", " ", txt)
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", txt)
    sentences = max(1, len(re.findall(r"[.!?](?:\s|$)", txt)))
    if len(words) < 50:
        return None

    def syl(w):
        n = len(re.findall(r"[aeiouy]+", w.lower()))
        if w.lower().endswith("e") and n > 1:
            n -= 1
        return max(1, n)

    wps = len(words) / sentences
    spw = sum(syl(w) for w in words) / len(words)
    return {"flesch": round(206.835 - 1.015 * wps - 84.6 * spw, 1),
            "grade": round(0.39 * wps + 11.8 * spw - 15.59, 1),
            "words": len(words)}


status = {
    "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
    "now": int(time.time()),
    "run_elapsed": run_elapsed(),
    "current_lap": current_lap(),
    "total_tokens": total_tokens(),
    "last_activity": last_activity(),
    "branch": sh("git", "rev-parse", "--abbrev-ref", "HEAD"),
    "last_commit": sh("git", "log", "-1", "--format=%h %s"),
    "tags": [t for t in sh("git", "tag", "-l", "--sort=v:refname", "--merged", "HEAD").splitlines() if t],
    "loop_running": bool(sh("pgrep", "-f", "harness/loop.sh")),
    "last_gates": last_gate_block(),
    "gate_history": gate_history(),
    "paper_log": paper_log(),
    "reviews": reviews(),
    "tokens": tokens_per_lap(),
    "agent_msg": newest_agent_msg(),
    "paper": paper_stats(),
    "readability": readability(),
    "drafts": drafts(),
    "todo": tail("TODO.md", 25),
    "editorial": tail("EDITORIAL.md", 20),
    "verify_tail": tail("VERIFY.log", 20),
}

(ROOT / "logs").mkdir(exist_ok=True)
(ROOT / "logs" / "status.json").write_text(json.dumps(status, indent=1))
print("status.json written", status["generated"])
