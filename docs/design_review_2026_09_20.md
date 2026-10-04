# Adversarial design review — 2026-09-20
 
Scope: every recorded decision in `context.md` / `project-plan.md`, checked against the code and files actually on disk. Claims in the docs were re-verified rather than taken on trust (parser re-run on the real `Valid.lean`/`Test.lean`; `repl_minif2f/REPL/{Main,JSON}.lean` read directly; git state inspected).
 
**What holds up.** The parser genuinely does what it says — 256/256 on `Valid.lean`, 244/244 on `Test.lean`, exactly one `sorry` per template except the two known `Test.lean` entries, header extraction correct on both splits (`Test.lean` correctly yields only `Nat`/`Real`, not Valid's four). The `open scoped` diagnosis, the `"\n\n"` terminator, the multi-line-response reader, the independent-env-per-attempt choice, the `attempt()`/`loop()` split, and the greedy-decoding root cause are all correct and well-reasoned. The bug log is unusually honest. Nothing below is a complaint about rigour; it's about the places where a correct local decision produces a wrong global result.
 
Findings are ranked by what they cost, not by how hard they are to fix.
 
---
 
## A. Soundness — the number you plan to report would be wrong
 
### A1. Nothing verifies that the model proved *your* theorem. (critical)
 
`loop()` asks for "the final, complete theorem (statement and proof)", `extract_proof()` returns that whole block, and `write_proof()` sends it to a base env that has `import MiniF2F.ProblemImports` but **not** `Valid.lean`. So the target name is undeclared, and the model is free to declare *anything* under it. `check()` only asks "were there errors? were there sorries?" — never "is this the theorem I asked for?"
 
Concretely, all of these score as a solved problem today:
- `theorem amc12a_2019_p21 : True := by trivial`
- the real statement with a hypothesis dropped, or `answer(36)` changed to whatever the model can actually prove
- a statement with `∀` weakened to a single instance
This is not hypothetical model malice — it's what a weak model *drifts into* when it retypes a long statement it can't prove, and the `answer(...)` value is sitting right there in the prompt to be edited. An unverified pass rate is the one output of Phase 1 that the whole CV story rests on.
 
**The incoherence:** the decision that opened this hole was recorded as a convenience. `context.md` says substituting into the template became *"moot — the final design doesn't substitute into the template at all, it re-sends the model's whole returned proof, since `write_proof` takes one complete string anyway."* But "`write_proof` takes one string" is an argument about the *wrapper's signature*, not about where that string should come from. Building the string from **your** trusted template plus the model's tactic block costs the same one call and closes the hole. The reasoning skipped a step: it justified *how* to send, and silently settled *what* to send.
 
**The design question:** do you close it by construction (extract only the tactic block, splice it into the parser's verbatim template) or by post-hoc checking (let the model send the whole thing, then ask Lean whether the declared constant's type is defeq to the reference statement)? The first is cheaper and is what most published harnesses do; the second is more robust to the model restructuring the statement legitimately (e.g. renaming binders). Either way, the pass criterion has to mention the reference statement somewhere, and right now it doesn't.
 
### A2. `check()` scores "Lean said nothing" as "proved". (critical)
 
The first branch — no `"messages"` **and** no `"sorries"` → `return 1` — is a blacklist. It assumes every non-proof outcome leaves a trace in one of those two keys. Three reachable paths where it doesn't:
 
1. **An empty or comment-only code block.** If the model emits ` ```lean4 ``` ` or a block containing only `-- omitted`, `extract_proof` returns `""` (not `None`, so the `proof == None` guard doesn't fire), Lean elaborates nothing, the response is `{"env": N}` — and that scores 1.
2. **A REPL-level error.** Confirmed in `repl_minif2f/REPL/JSON.lean:169`: `structure Error where message : String` — **singular `message`**. `runCommand` returns one for `"Unknown environment."` and for any exception during `IO.processInput` (`Main.lean:302-308`). None of those responses contain `messages` or `sorries`. All of them score 1.
3. **Any valid-but-irrelevant declaration** — see A1.
The fix direction is to invert it: success should require positive evidence (an `env` in the response, zero `severity == "error"` messages, zero `sorries`, and the target declaration actually present in the new environment), with everything else an explicit failure or an explicit "harness error" verdict distinct from "model failed". Right now a broken harness and a solved problem are the same number.
 
Note also the ordering interaction with A1: because 1 is returned before any of the interesting checks, every one of these paths inflates the pass rate in the direction that flatters the project.
 
### A3. No axiom check — `sorry` is caught, the other escape hatches aren't. (high)
 
`sorries` catches `sorry`. It does not catch `native_decide` (which discharges goals through the compiler via `ofReduceBool`, a different trust story and explicitly excluded by most prover benchmarks), and it does not catch the model declaring its own `axiom` or `@[simp] lemma foo : <the goal> := sorry` in a *separate* command… actually the latter would show a sorry, but an `axiom` declaration would not.
 
Standard practice is one extra REPL round-trip on each success: `#print axioms <name>`, and accept only if the axiom set is contained in `{propext, Classical.choice, Quot.sound}`. It costs one near-instant call per *solved* problem — i.e. almost nothing — and it's the single cheapest thing you can put in the writeup to show you knew this was a risk. Worth deciding now, because retrofitting it means re-running the baseline.
 
---
 
## B. The run will not survive to completion
 
### B1. There is no timeout anywhere in the Lean path. (high)
 
`LEANRepl.send()` blocks on `self.proc.stdout.readline()` with no deadline. Lean has no shortage of ways to not come back: `decide` on a large `Nat`, `nlinarith` with too many hypotheses, a looping `simp` set, `Finset.sum` over something that unfolds badly. A model that is bad at Lean produces exactly these. One hang stops the whole 256-problem run with no diagnostic, and `time_budget_seconds` won't save you — it's checked between attempts, never during one.
 
A per-command deadline (and a `maxHeartbeats`/`maxRecDepth` option in the submitted command, which is the Lean-side half of the same guard) needs to exist before any unattended run.
 
### B2. A dead REPL takes the run with it, loudly and then confusingly. (high)
 
`send()`'s EOF path prints `"error on LEAN answer!!"`, breaks, and then does `json.loads("")` — a `JSONDecodeError` from a line that has nothing to do with the actual cause. The REPL can die for real reasons: `parse` throws `IO.userError` on unparseable input and nothing catches it (`Main.lean:396`, `412`), and see B3 for memory. There's no supervision, no restart, no re-import of the base env. Over an 85-hour run (see C1) this is not a tail risk.
 
### B3. The REPL's memory grows without bound, by design. (medium-high)
 
`recordCommandSnapshot` (`Main.lean:86-89`) pushes every command's environment onto `cmdStates : Array CommandSnapshot`, and nothing ever removes one. Each is a full post-Mathlib environment snapshot. Your independent-env-per-attempt design is correct, but it means roughly 3 snapshots per problem × 256 problems ≈ 770 retained environments, in 32GB of unified memory that is simultaneously holding an 8B model. Every `sorry` additionally records a `ProofSnapshot`.
 
Mitigation is cheap and doesn't change the design: restart the REPL every N problems and re-import (or pickle the base env once and unpickle into a fresh process). But it needs to be a decision, not a surprise at problem 180.
 
### B4. Nothing is written to disk, and the thing being discarded is Phase 2's training set. (high)
 
`loop()` returns `(check, proof)` on success and an implicit `None` otherwise. No per-problem record, no raw model output, no Lean errors, no attempt count, no timing, no resumability. Two separate consequences:
 
- **Operationally:** an 85-hour run that dies at hour 60 loses everything, and you can't restart it from problem 181.
- **Structurally, and this is the bigger one:** the Goedel recipe you've written into Phase 2 works by *keeping the Lean-verified proofs and folding them back into training data*. Those proofs are being generated by the baseline run and thrown away. The baseline run and the first expert-iteration harvest are the same computation, and right now only one of them is being collected. Per-problem JSONL (name, attempt index, raw text, extracted proof, Lean response, verdict, wall-clock, tokens) turns a 3.5-day baseline into a 3.5-day baseline *plus* a seed SFT set, for the cost of a file handle.
This is the highest value-per-effort item in the whole review.
 
---
 
## C. Compute and configuration — the arithmetic doesn't close
 
### C1. The per-problem budget is off by ~2×, and the schedule by ~an order of magnitude. (high)
 
Using your own measured 29.5 tok/s on `Qwen3-8B-4bit`: a full 12,000-token attempt is **~407 s ≈ 6.8 min**. With `time_budget_seconds = 600` and the first attempt deliberately outside the budget, the loop runs attempt 1 (~6.8 min, uncounted), then checks `elapsed = 0 < 600` → attempt 2 (~6.8 min), then `elapsed ≈ 407 < 600` → attempt 3, exiting at ~13.6 min elapsed. So **~3 attempts, ~20 min per problem**, not 10.
 
- `dev_subset_25`: ≈ **8 hours**
- full `Valid.lean` (256): ≈ **85 hours ≈ 3.5 days** of uninterrupted laptop compute
Against a roadmap that says "Phase 1 (this week)" and includes the baseline run, a mathlib mining step, *and* a LoRA fine-tune. The budget number isn't wrong so much as it was never reconciled with the token budget it has to coexist with — `context.md` correctly records that the minutes-per-problem number was "still open… needs picking once real tokens/sec is known", and then 29.5 tok/s was measured and the reconciliation never happened.
 
### C2. The context window caps retries below what the budget allows, so the budget is measuring something that can't occur. (high)
 
`loop()` appends the full `raw_text` — up to 12,000 tokens, `<think>` block included — to `messages` on every retry. Qwen3-8B is 32,768 tokens natively (131k only with YaRN, which `mlx-lm` won't enable for you; worth confirming from the model's `config.json` → `max_position_embeddings`). So by attempt 3 you need roughly 24k of history + 12k of new generation ≈ 36k > 32k.
 
Two conclusions. First, the retry loop structurally cannot exceed ~2 retries no matter what `time_budget_seconds` says — so the "time budget, not a fixed try-count" decision, whose whole rationale was *"a trivial one-liner and an IMO-tier problem don't deserve the same number of attempts"*, delivers roughly the same fixed small count for everything anyway. The choice isn't buying what it was chosen to buy. Second, the failure mode when you cross the line is silent (`mlx-lm` truncates or errors depending on version), and it'll happen on exactly the hard problems where retries matter most.
 
The open item already logged as *"whether growing per-retry context length needs any mitigation"* is not an optimisation question — it's the binding constraint on the retry design. Candidates: don't append `<think>` (verify the template's stripping behaviour first — your logged tokenizer-only test is the right experiment and costs nothing), or keep only the last attempt + its error rather than the full transcript, or make retries stateless with error feedback only.
 
### C3. The baseline's default config is the only one with zero observed successes. (high)
 
From your own logs:
 
| config | outcome | cost |
|---|---|---|
| thinking on, 12k, greedy | degenerate repetition, no Lean at all | full 12k budget |
| thinking on, 12k, fixed sampler (`test.ipynb`) | `"Model didn't give a complete answer"` — no fence | full 12k budget |
| thinking off | complete, well-formed Lean (wrong, but parseable) | **37 s, 1092 tokens** |
 
`retry_loop.py` hardcodes the first column at the call site. Thinking-on is 0-for-2 on producing anything extractable and costs **11× more compute per attempt** than the configuration that worked. At a fixed compute budget that's ~11 non-thinking attempts against 1 thinking attempt — and for miniF2F specifically, the literature is fairly consistent that many cheap independent samples beat one long expensive one at this model scale.
 
This one is cheap to settle empirically and would be a good result in the writeup on its own: run dev-subset A/B (thinking on ~3 attempts vs thinking off ~30 attempts, equal wall-clock). The open question is already logged; it just needs to be answered *before* 85 hours are spent on the arm that has never worked.
 
### C4. A wall-clock stopping rule makes the headline delta non-reproducible. (high)
 
The reportable number is "same model, before my training vs after". Under a time budget, the number of attempts each arm gets depends on thermal throttling, background load, context growth, and the generation-speed difference between the base model and the LoRA-adapted one (adapters are slower). Two runs of the *same* model on the same day can differ; base-vs-fine-tuned differ systematically in a direction unrelated to proof ability.
 
The reasoning behind the time budget (harder problems deserve more attempts) is sound but it's optimising the wrong thing for a *benchmark*: allocation policy belongs in a system you're deploying, not in the measuring instrument. A fixed attempt count (pass@k, with k fixed across both arms) with wall-clock *recorded as a second column* gives you both the reproducible number and the efficiency story. You can keep the time budget as a hard safety cap so one pathological problem can't eat the run.
 
### C5. The repetition penalty is an unvalidated confound. (medium)
 
`repetition_penalty=1.1, repetition_context_size=64` was introduced in the same change as the sampler fix, so neither has been isolated. Qwen's own recommendation is the sampler settings; the penalty is yours. And Lean proofs legitimately repeat tokens at short range — `norm_num` / `simp` / `linarith` in sequence, `have h₁ : … have h₂ : … have h₃ : …`, repeated `Finset.sum` / `Complex.I` mentions. A 64-token window penalising exactly that is plausibly suppressing valid syntax, which would show up as the "syntactically well-formed but subtly malformed" failures you'd otherwise attribute to the model.
 
Worth one dev-subset run with the penalty off to check it isn't costing you. If it is load-bearing, that's a finding; if it isn't, drop it and remove a variable from the baseline.
 
### C6. No seed, no repeats, no interval. (medium)
 
Sampling at temp 0.6–0.7 across 256 problems has real run-to-run variance, and nothing sets `mx.random.seed` or plans a repeat. If the fine-tuned model comes in at +4 points, you currently have no way to say whether that's a result or noise. At minimum: fix and record a seed, and report a Wilson interval on the pass rate (on 256 problems, ±5–6 points at typical rates — which is roughly the size of the effect you're hoping to measure). Ideally 2–3 seeds on the dev subset to get a variance estimate cheaply.
 
---
 
## D. Evaluation design — coherence problems
 
### D1. `Valid.lean` can't be both the reported baseline and Phase 2's training set. (high)
 
Phase 2 is expert iteration: generate on problems, keep the Lean-verified proofs, train on them, repeat. The problems are `Valid.lean`'s 256. After one iteration, `Valid.lean` is literally training data — and "baseline on Valid vs fine-tuned on Valid" becomes train-on-test.
 
`Test.lean` is correctly held out, but the plan only reaches for it *"until a final honest number is needed"* — by which time you'll have no pre-training baseline on it to compare against, because you'll have to run one on a model you've already trained.
 
**The cheap fix, available only right now:** run the zero-shot baseline on `Test.lean` **once**, before any training, at the same time as the Valid baseline. A zero-shot pass doesn't contaminate anything provided you don't inspect per-problem failures to tune prompts. Then your headline is a clean Test→Test delta, and Valid is free to be dev/train throughout. Doing this costs one extra run now; not doing it costs the headline number later.
 
### D2. Your own train/inference-mismatch principle is applied once and violated three times. (high)
 
The reasoning for discarding informal statements is exactly right: *"the model will only ever be given the formal Lean statement at inference time, so training or prompting it with the informal text would create a train/inference mismatch."* Hold the rest of the plan to that standard:
 
1. **SFT on mathlib, eval in a multi-turn error-feedback loop.** Mined mathlib proofs are single-turn. Nothing in that data teaches the model to consume a Lean error message and revise. You'd be training the first-attempt skill and measuring a first-attempt-plus-repair skill.
2. **SFT data has no `<think>` blocks; inference runs `enable_thinking=True`.** If C3 lands on thinking-on, you'd be fine-tuning a model out of the format it's being evaluated in.
3. **Mathlib's surface form is not miniF2F's.** Library lemmas with namespaces and structured `calc`/`simp only` idioms, versus competition statements with `h₀ h₁ h₂` hypothesis naming and `answer(...)` wrappers. Same mismatch argument, different axis.
None of these is fatal, and each has a cheap answer (include repair turns in the SFT data; match the thinking format; reformat mined proofs into the target shape). What matters is applying the principle uniformly — a reviewer who reads your informal-statement rationale will ask about these three immediately, and having an answer is worth more than having avoided the question.
 
### D3. Report pass@1 and pass@retry separately, or the delta isn't attributable. (medium-high)
 
Mathlib SFT plausibly improves first-attempt proof writing and does approximately nothing for error-feedback use. Collapsing both into one number hides where the gain came from — and the decomposition is the better story: "+X points on first attempt from fine-tuning, +Y points from the retry loop, and here's which problems only the loop solves". That's two results instead of one, from the same run, and it requires nothing but logging the per-attempt verdict (which B4 gives you anyway).
 
### D4. `dev_subset_25`'s pass rate is not an estimate of anything. (medium)
 
It's stratified by difficulty *by construction* (6/12/5/2), so its pass rate doesn't estimate the Valid pass rate — it estimates a distribution you invented. Its own `_meta` correctly says it's for iteration and not the final scope; the risk is purely that an 8-hour dev number gets quoted somewhere later because it's the only number that exists for weeks. Worth writing "never reported" into the file itself, and worth considering a *random* 25–30 alongside it so you have a cheap unbiased read during development.
 
### D5. `dev_subset_25.json` is stale and contradicts two later decisions. (medium — but it's step 4 of the plan)
 
Verified against the file on disk:
 
- **All 25 entries carry an `informal_statement` field.** Superseded by the "no informal statement, docstrings fully discarded" decision.
- **All 25 `lean_statement`s end at `:= by` with the `sorry` stripped.** The pipeline now feeds the parser's full template *including* the trailing `sorry` — and that's the exact shape the prompt wording ("Replace `sorry` with a real proof") and `extract_proof` were designed and tested against. Feeding these instead would silently change the prompt you measured.
- **It duplicates statement text that `parser.py` is the source of truth for**, so the two can drift (and have).
Plan step 4 consumes this file. It should carry names only, and look the statements up through the parser.
 
### D6. Contamination and comparability, for the writeup. (medium)
 
miniF2F valid *and* test are public GitHub files and are almost certainly in Qwen3's pretraining corpus. This doesn't invalidate a same-model before/after delta — which is precisely why your baseline choice is the right one — but a portfolio piece that doesn't name the issue invites the first question a reviewer will ask. One paragraph, stating it and explaining why the delta survives it, converts a liability into evidence of judgement.
 
Relatedly: the DeepMind fork has corrected formalizations, `answer(...)` wrappers, and a `formal_conjectures` dependency, so its statements are **not** the ones Goedel-Prover-V2 / DeepSeek-Prover-V2 report against. Cite their numbers as ceiling context by all means, but say they're on a different variant of the benchmark.
 
### D7. Is mathlib the right SFT source at all? (open question, worth deciding before mining)
 
Goedel and DeepSeek got their gains primarily from autoformalized *competition-style* problems plus expert iteration, not from raw mathlib. Given D2.3 and given that expert iteration produces data already in exactly the target format, the honest question is whether mathlib mining is the best use of the Phase-1 slot — or whether the seed SFT set should come from the baseline run's own verified successes (B4), with mathlib as a supplement rather than the foundation. Worth answering deliberately, since it's a week of work either way.
 
---
 
## E. Repo and artifact hygiene (weighted up, because this is a CV piece)
 
1. **`repl/` is a stale duplicate clone of the REPL, pinned to `leanprover/lean4:v4.33.1`** against the project's `v4.27.0`. It's tracked by git as an embedded repo with **no `.gitmodules` entry** (`.gitmodules` lists only `miniF2F` and `repl_minif2f`), so a `git clone --recursive` by anyone else produces a broken or empty directory. `.gitignore` covers `repl_minif2f/.lake/` but not `repl/.lake/`. Delete it, or make it a real submodule — but the toolchain mismatch is also a live foot-gun for anyone who edits the path in `wrapper.py`.
2. **Generated files are written into the miniF2F submodule.** `drop_comments` writes `Valid_parser.lean` / `Test_parser.lean` next to the source, and there's a stale `parser.lean` (byte-identical size to `Valid_parser.lean`) still sitting there. Confirmed effect, from `.git/COMMIT_EDITMSG`: `modified: miniF2F (modified content, untracked content)`. Generated artifacts belong outside the submodule, in a `data/` or `build/` directory the parent repo controls.
3. **Hardcoded absolute paths in `wrapper.py`, `model.py`, `retry_loop.py`.** `wrapper.py` also mixes an absolute `cwd` with a relative `../repl_minif2f/...` binary path, so it works from one directory and one machine. For a repo whose purpose is to be read by a stranger, "clone and it can't run" is a real cost.
4. **`retry_loop.py` runs at import.** Lines 137–151 are top-level: importing the module loads an 8B model and spawns a Lean REPL. And `test.ipynb` contains its own pasted copy of `extract_proof` and `loop` — two implementations already diverging (the notebook's `loop` has no time budget). One of them should be the source.
5. **`parser.py` shadows a stdlib module name** (`parser` was a CPython builtin until 3.10 — fine on 3.10+, a real collision below), and `import_project` uses `open` as a loop variable, shadowing the builtin inside that method. Neither bites today; both are exactly the kind of thing that bites at 2am.
6. **`README.txt` still says "No training required — the engineering is in the loop, the prompting, and the retry logic."** Superseded on 2026-08-25, flagged as your task in `project-plan.md`, still open. It's the first thing anyone reads.
7. **Two diverging `context.md`.** The file on disk (507 lines) predates the project-doc copy — it stops at "confirms the pipeline works correctly on the failure path" and has none of the `attempt()`/`loop()` split. Pick one as the source of truth; a stale context file is worse than none, because it gets trusted.
8. **No `requirements.txt` / environment file**, despite a documented multi-session fight with conda and `PATH`. The `runlean` alias lives in `~/.zshrc` — invisible to a clone, and the single most likely thing to break for anyone (including future you on a new machine).
9. Branch is 2 commits ahead of `origin/main`, unpushed.
---
 
## F. Smaller code-level items
 
- **`extract_proof` fence matching is brittle**: only ` ```lean4 ` matches — ` ```lean `, ` ```Lean4 `, or a bare ` ``` ` all yield `None` and are scored as "model gave no answer". Given C3's finding that "no complete answer" is currently your dominant failure mode, it's worth knowing how much of that is the model versus the anchor. The `+8` magic number is the same fragility in miniature. Also: an unclosed *final* fence discards an earlier *complete* block, which is the case where the model committed to an answer and then kept talking.
- **`errors = answer["messages"]`** is interpolated by raw repr and unfiltered — the model sees Python dict syntax including `info`/`warning` entries. Your logged concern about overwhelming it with 3+ independent errors is real; the first `severity == "error"` with its position, rendered as text, is the obvious first thing to try. This is the highest-leverage untested knob in the retry loop — the whole premise of retrying is that the feedback is usable.
- **`loop()` falling off the end returns an implicit `None`**, colliding with `attempt()`'s "no answer" `None`. Given A2, the general principle worth adopting: every distinguishable outcome gets a distinguishable value, and "I don't know what happened" is never spelled the same way as "it worked" or as a specific known failure.
- **`attempt()`'s `verbose` never reaches `generate()`** (known) — which matters more than it looks, because with C1's 6.8-minute attempts you currently have no way to see a run is alive.
- **`check`/`proof` compared with `== None`** rather than `is None`.
- **No stagnation detection**: nothing stops the model resubmitting a byte-identical failing proof every retry. Logging the repeat rate would tell you whether the retry loop is doing anything at all — and it's a genuinely interesting number for the writeup.
- **The subprocess's `stderr` isn't captured**, so `lake`/Lean diagnostics vanish into the terminal instead of a log.
- **No `try`/`finally` around `Repl.close()`** in `retry_loop.py`: an exception leaves an orphan REPL holding a full Mathlib environment in memory, which is the documented reason `close()` exists.
- **`import_project`'s response isn't checked** before `response["env"]` (known). With A2's inverted check it becomes a non-issue; until then it fails as a bare `KeyError`.
---
 
## Suggested order
 
Ordered by what unblocks or invalidates the most downstream work, not by effort:
 
1. **B4 (logging + resumability)** — cheapest, and it's a prerequisite for Phase 2 rather than a nicety.
2. **A1 + A2** — before any number is generated, because they invalidate every number generated before them.
3. **C3 (thinking on/off A/B) and C2 (context cap)** — before committing 85 hours to a configuration with zero observed successes.
4. **C4 (pass@k instead of wall-clock) + C6 (seed)** — before the baseline, because the baseline defines the protocol the fine-tuned run must match.
5. **D1 (baseline on `Test.lean` too, once, now)** — the window for this closes permanently the moment training starts.
6. **A3, B1–B3** — before the first unattended multi-hour run.
7. **D5, E1–E8** — whenever; low risk, and E is what a reader sees first.
 
