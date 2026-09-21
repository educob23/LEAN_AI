import argparse
import json
import time
from pathlib import Path

import parser
import wrapper
from retry_loop import loop

from mlx_lm import load


PATH_TO_VALID = "/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Valid.lean"
PATH_TO_VALID_PARSED = "/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Valid_parser.lean"


def load_done(results_path):
    """
        Reads results_path (jsonl, one record per already-attempted theorem this batch
        or a previous one) and returns {theorem_name: record}. Used so an interrupted
        run can be re-launched without redoing theorems it already finished.
    """
    done = {}
    p = Path(results_path)
    if p.exists():
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                done[rec["theorem"]] = rec
    return done


def run_batch(time_budget_per_theorem=600, max_tokens=5000, enable_thinking=False,
              results_path="valid_results.jsonl", attempts_logfile="attempts.jsonl",
              verbose=True):
    """
        Runs loop() unsupervised over every theorem in MiniF2F's Valid set and appends
        one summary record per theorem to results_path as it goes.

        Safe to re-launch after being killed: theorems already present in results_path
        are skipped, so nothing gets redone. A Lean REPL hang/crash on one theorem
        restarts the REPL (handled inside attempt()/loop()) and marks that theorem
        failed with check == "repl_crash", rather than stopping the whole batch. Any
        other unexpected exception is also caught per-theorem as a last-resort safety
        net, for the same reason: nothing should be able to take down an unsupervised
        run except the machine itself.
    """
    parser.drop_comments(PATH_TO_VALID, "Valid")
    imports, opens = parser.treat_header(PATH_TO_VALID_PARSED)
    theorems = parser.extract_theorems(PATH_TO_VALID_PARSED)

    done = load_done(results_path)
    remaining = {name: thm for name, thm in theorems.items() if name not in done}

    print(f"{len(theorems)} theorems total, {len(done)} already attempted "
          f"(resuming from {results_path}), {len(remaining)} left to run.")

    Repl = wrapper.LEANRepl()
    Repl.import_project(imports, opens)

    model, tokenizer = load("mlx-community/Qwen3-8B-4bit")

    solved = sum(1 for r in done.values() if r.get("solved"))
    start_all = time.monotonic()

    try:
        for i, (name, thm) in enumerate(remaining.items(), 1):
            print(f"[{i}/{len(remaining)}] {name}")
            t0 = time.monotonic()

            try:
                result = loop(thm, Repl, model, tokenizer, enable_thinking=enable_thinking,
                               max_tokens=max_tokens, verbose=verbose,
                               time_budget_seconds=time_budget_per_theorem,
                               logfile=attempts_logfile)
                check, proof = result
            except Exception as e:
                # Nothing anticipated should reach here (loop()/attempt() already
                # handle Lean crashes) — this is only a last-resort net so a truly
                # unforeseen bug still can't kill an unsupervised run.
                print(f"  unexpected error on {name}: {e!r} — restarting REPL, marking failed")
                try:
                    Repl._restart()
                except Exception as restart_err:
                    print(f"  REPL restart also failed: {restart_err!r} — "
                          f"spawning a brand new one")
                    Repl = wrapper.LEANRepl()
                    Repl.import_project(imports, opens)
                check, proof = "unexpected_error", None

            elapsed = time.monotonic() - t0
            record = {
                "theorem": name,
                "solved": check == 1,
                "check": check,
                "proof": proof,
                "elapsed_s": elapsed,
                "ts": time.time(),
            }
            with open(results_path, "a") as f:
                f.write(json.dumps(record) + "\n")

            if check == 1:
                solved += 1
                print(f"  solved ({elapsed:.0f}s)")
            else:
                print(f"  not solved [{check}] ({elapsed:.0f}s)")

    finally:
        Repl.close()

    attempted = len(done) + len(remaining)
    print(f"\nDone. {solved}/{attempted} solved out of {len(theorems)} theorems in Valid "
          f"({time.monotonic() - start_all:.0f}s this run). Results in {results_path}.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Unsupervised batch run over MiniF2F Valid.")
    ap.add_argument("--time-budget", type=int, default=600,
                     help="seconds allowed per theorem (default 600)")
    ap.add_argument("--max-tokens", type=int, default=5000)
    ap.add_argument("--results", default="valid_results.jsonl",
                     help="jsonl file for per-theorem outcomes; also used to resume")
    ap.add_argument("--attempts-log", default="attempts.jsonl",
                     help="jsonl file for per-attempt raw logs (as in loop())")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    run_batch(time_budget_per_theorem=args.time_budget, max_tokens=args.max_tokens,
              results_path=args.results, attempts_logfile=args.attempts_log,
              verbose=not args.quiet)
