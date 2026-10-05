# Roadmap

This is the plan the project follows. It is updated as the work moves forward.
**Last update: 2026-10-05.**

**Goal:** turn a general open-weight model (`Qwen3-8B`) into a better formal prover. The
result is measured as an honest *before vs. after training* comparison: same model, same
problems, same protocol, and every proof checked by Lean.

**Principles that shape the plan**

- **Measure before you train.** The reference point is the model's own zero-shot score.
  Comparing against other, bigger systems would say little about my own work.
- **Keep the test set clean.** miniF2F-test is used once for a zero-shot score before any
  training, and then only for the final evaluation. All development happens on
  miniF2F-valid.
- **Nothing counts unless Lean accepts it.** That includes an identity check against the
  original statement, and soon an axiom audit.
- **One laptop.** Everything runs on an Apple M1 Max (32 GB) with MLX. Choices like 4-bit
  inference, LoRA and a model of about 8B parameters follow from that.

---

## Phase 0 — Infrastructure ✅ *(Aug 25 → Sep 21, 2026)*

| Step | Status |
|---|---|
| Choose the tools: Lean REPL (over LeanDojo and Pantograph), the DeepMind miniF2F fork, Lean `v4.27.0` | ✅ |
| Lean 4 + Mathlib toolchain; REPL built and pinned to the same toolchain | ✅ |
| Python ↔ Lean REPL interface (`wrapper.py`) | ✅ |
| Problem parser (`parser.py`), checked on 256/256 valid and 244/244 test problems | ✅ |
| Base model chosen: `Qwen3-8B` (Goedel-Prover-V2-8B is built on the same family) | ✅ |
| Generate → verify pipeline, DeepSeek-Prover-style prompt, non-greedy sampling | ✅ |
| Adversarial design review of the evaluation; soundness fixes (identity check, harness errors) | ✅ |
| Retry loop with Lean error feedback; crash/timeout recovery; resumable batch runner | ✅ |

## Phase 1 — Baseline and first fine-tune 🔄 *(current)*

| Step | Status |
|---|---|
| **1a.** Zero-shot baseline on miniF2F-valid (256 problems, 300 s per problem) | ✅ **done** (2026-10-05): **17/256 solved (6.6 %)**, 9 on the first attempt ([summary](results/2026-10-04_baseline_qwen3-8b_valid_300s/SUMMARY.md)) |
| **1b.** Fix the evaluation protocol for the before/after comparison: a fixed number of attempts (pass@k) instead of a time budget, a fixed random seed, and a thinking-mode on/off comparison on the 25-problem dev subset | ⏳ next |
| **1c.** Axiom audit of every accepted proof (`#print axioms`) | ⏳ |
| **1d.** One-time zero-shot score on miniF2F-test, before any training | ⏳ |
| **1e.** Build the fine-tuning dataset: the Lean-verified proofs from the baseline, plus up-to-date Lean 4 / Mathlib proofs | ⏳ |
| **1f.** LoRA fine-tune of Qwen3-8B with `mlx-lm` on the M1 Max | ⏳ |
| **1g.** Re-evaluate with the exact same protocol and publish the before/after comparison | ⏳ |

**What the baseline says about 1e.** The model almost always produces a
well-formed answer, but Lean rejects 98 % of attempts. 11 % of the proofs use Lean 3
syntax, and 35 % of the rejections call lemmas that don't exist (details in
[results](results/2026-10-04_baseline_qwen3-8b_valid_300s/SUMMARY.md)). So the fine-tuning
data has to be current Lean 4 / Mathlib: these are knowledge errors, not formatting errors.

**Deliverable:** the before/after table on valid and test, the training data recipe, and a
short write-up.

## Phase 2 — Expert iteration ⏳

The model attempts problems; proofs that Lean verifies go back into the training data; the
model is retrained; repeat. This is the recipe behind Goedel-Prover.

- Track the pass rate after each iteration. That curve is the main result of this phase.
- This is also where the retry design becomes more agentic: the model calls the Lean
  checker itself in the middle of its reasoning.

## Phase 3 — Reinforcement learning with Lean as the reward ⏳ *(stretch)*

GRPO-style RL with Lean pass/fail as the reward, starting from the fine-tuned model (the
approach of DeepSeek-Prover-V2). This phase is deliberately last, because it is the
hardest to get stable.

---

## Decision log (short)

| Date | Decision | Why |
|---|---|---|
| 2026-08-25 | Specialize an open-weight model instead of only prompting a closed API | Fine-tuning needs open weights, and a real improvement has to come from training |
| 2026-08-25 | Lean REPL as the verifier | Mathlib stays loaded in memory, so each check is fast; simpler than LeanDojo for this scope |
| 2026-09 | `Qwen3-8B` (instruct, 4-bit, MLX) | Strong math and code priors (the base of Goedel-Prover-V2-8B); fits in 32 GB; instruct avoids formatting problems on a first fine-tune |
| 2026-09 | Baseline = the same model, zero-shot | Gives a before/after difference that is entirely attributable to my training |
| 2026-09-20 | Identity check on every candidate proof | The model could otherwise "prove" an easier statement under the right name |
| 2026-09-21 | Lean error feedback in a multi-turn retry loop | Lean's error messages tell the model exactly what is wrong. Confirmed by the baseline: 9 → 17 solved with retries |

Full design history: [`docs/`](docs/).
