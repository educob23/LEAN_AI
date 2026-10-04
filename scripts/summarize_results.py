"""
Summarize one run directory produced by run_batch.py.

    python scripts/summarize_results.py results/2026-10-04_baseline_qwen3-8b_valid_300s

Reads `results.jsonl` (one record per theorem) and, if present, `attempts.jsonl`
or `attempts.jsonl.gz` (one record per model attempt), prints a Markdown summary
and writes it to `<run_dir>/SUMMARY.md`. Standard library only.
"""
import argparse
import collections
import gzip
import json
import statistics
from pathlib import Path

SOURCES = [  # (name prefix, label) -- first match wins
    ("mathd_algebra", "MATH — algebra"),
    ("mathd_numbertheory", "MATH — number theory"),
    ("amc12", "AMC 12"),
    ("aime", "AIME"),
    ("imo", "IMO"),
    ("", "Custom (algebra / number theory / induction)"),
]

# Lean error message (first line) -> failure category. Checked in order.
ERROR_CATEGORIES = [
    ("Hallucinated name (unknown identifier / constant / field)",
     ("Unknown identifier", "Unknown constant", "unknown identifier", "unknown constant",
      "Invalid field", "does not contain")),
    ("Syntax error (often Lean 3 / old Mathlib syntax)",
     ("unexpected token", "unexpected identifier", "Invalid `end`", "unknown tactic",
      "must be used in the beginning of the file", "Invalid syntax")),
    ("Type error", ("Type mismatch", "type mismatch", "failed to synthesize",
                    "Function expected")),
    ("Tactic failed / goals left open", ("unsolved goals", "failed", "made no progress",
                                         "No goals", "did not find")),
]


def read_jsonl(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def source_of(name):
    for prefix, label in SOURCES:
        if name.startswith(prefix):
            return label
    return SOURCES[-1][1]


def categories_of(answer):
    errors = [m.get("data", "") for m in (answer or {}).get("messages", [])
              if m.get("severity") == "error"]
    found = set()
    for msg in errors:
        first = msg.split("\n", 1)[0]
        for label, needles in ERROR_CATEGORIES:
            if any(n in first for n in needles):
                found.add(label)
                break
        else:
            found.add("Other")
    return found


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


def summarize(run_dir, total):
    run_dir = Path(run_dir)
    results = read_jsonl(run_dir / "results.jsonl")
    # keep the last record per theorem (a resumed run never duplicates, but be safe)
    results = list({r["theorem"]: r for r in results}.values())
    n = len(results)
    solved = [r for r in results if r.get("solved")]

    attempts = None
    for name in ("attempts.jsonl", "attempts.jsonl.gz"):
        if (run_dir / name).exists():
            attempts = read_jsonl(run_dir / name)
            break

    out = [f"# Run summary — `{run_dir.name}`", ""]
    status = "complete" if n >= total else f"**partial — {n}/{total} theorems evaluated**"
    out += [f"Status: {status}.", ""]

    out += ["| Metric | Value |", "|---|---|"]
    out.append(f"| Theorems evaluated | {n} / {total} |")
    out.append(f"| Solved (Lean-verified) | **{len(solved)} / {n} ({pct(len(solved), n)})** |")

    if attempts is not None:
        by_thm = collections.defaultdict(list)
        for a in attempts:
            by_thm[a["theorem"]].append(a)
        evaluated = {r["theorem"] for r in results}
        first_ok = sum(1 for t in evaluated
                       if any(a["attempt"] == 0 and a["check"] == 1 for a in by_thm.get(t, [])))
        out.append(f"| Solved on the first attempt (pass@1) | {first_ok} / {n} ({pct(first_ok, n)}) |")
        out.append(f"| Solved only after Lean-feedback retries | {len(solved) - first_ok} |")
        counts = [len(by_thm[t]) for t in evaluated if t in by_thm]
        if counts:
            out.append(f"| Model attempts (total / median per theorem) | "
                       f"{sum(counts)} / {statistics.median(counts):g} |")
        durations = [a["elapsed_s"] for a in attempts if a["theorem"] in evaluated]
        if durations:
            out.append(f"| Median time per attempt (generation + Lean check) | "
                       f"{statistics.median(durations):.0f} s |")
    if solved:
        out.append(f"| Median time to a verified proof | "
                   f"{statistics.median(r['elapsed_s'] for r in solved):.0f} s |")
    out.append("")

    # by problem source
    by_src = collections.defaultdict(lambda: [0, 0])
    for r in results:
        s = by_src[source_of(r["theorem"])]
        s[1] += 1
        s[0] += bool(r.get("solved"))
    out += ["## By problem source", "", "| Source | Solved | Evaluated | Rate |", "|---|---|---|---|"]
    for _, label in SOURCES:
        if label in by_src:
            s, t = by_src[label]
            out.append(f"| {label} | {s} | {t} | {pct(s, t)} |")
    out.append("")

    # outcome of every attempt + failure categories
    if attempts is not None:
        evaluated = {r["theorem"] for r in results}
        atts = [a for a in attempts if a["theorem"] in evaluated]
        names = {1: "Verified proof", -1: "Rejected by Lean", 0: "Contains `sorry`",
                 None: "No complete ```lean4 block"}
        oc = collections.Counter(names.get(a["check"], str(a["check"])) for a in atts)
        out += ["## Outcome of individual attempts", "", "| Outcome | Attempts | Share |",
                "|---|---|---|"]
        for k, v in oc.most_common():
            out.append(f"| {k} | {v} | {pct(v, len(atts))} |")
        out.append("")

        rejected = [a for a in atts if a["check"] == -1]
        cat = collections.Counter()
        for a in rejected:
            cat.update(categories_of(a.get("answer")))
        out += ["## Why Lean rejected attempts", "",
                "Share of rejected attempts containing at least one error of each kind "
                "(an attempt can fall in several).", "",
                "| Error kind | Rejected attempts | Share |", "|---|---|---|"]
        for k, v in cat.most_common():
            out.append(f"| {k} | {v} | {pct(v, len(rejected))} |")
        out.append("")

    out += ["## Solved theorems", ""]
    for r in sorted(solved, key=lambda r: r["theorem"]):
        out.append(f"- `{r['theorem']}` ({r['elapsed_s']:.0f} s)")
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run_dir")
    ap.add_argument("--total", type=int, default=256,
                    help="number of theorems in the evaluated split (default: 256, miniF2F valid)")
    ap.add_argument("--no-write", action="store_true", help="print only, don't write SUMMARY.md")
    args = ap.parse_args()
    md = summarize(args.run_dir, args.total)
    print(md)
    if not args.no_write:
        (Path(args.run_dir) / "SUMMARY.md").write_text(md + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
