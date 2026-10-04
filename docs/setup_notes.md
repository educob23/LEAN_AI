# Setup notes — LLM-assisted Lean proof generation
 
Captured 2026-08-25, before any scaffolding started. This is prep research, not a build log.
 
## Status as of now
Nothing built yet. Checked the workspace: no `lean`/`elan`/`lake` installed anywhere, no dataset pulled in, no orchestration code, no LLM API wired up. README defines the scope; everything below is what needs to exist before the first candidate proof gets checked.
 
## What the pipeline needs
1. **Lean 4 toolchain** — via `elan`, plus a `lake` project that depends on mathlib (most miniF2F-style problems need mathlib lemmas).
2. **A way to feed candidate proofs to Lean and read back pass/fail + error text**, for the retry loop.
3. **A benchmark dataset** — a Lean 4 port of miniF2F.
4. **An LLM API** for proposing candidate proof steps.
5. **Orchestration code** — the actual loop: prompt → Lean check → feed errors back on failure → retry (bounded), log each attempt.
## Lean interaction — options considered
- **Bare `lake env lean` per attempt** — simplest, but re-elaborates the whole environment (with mathlib) every time. Slow for a retry loop.
- **Lean REPL** ([leanprover-community/repl](https://github.com/leanprover-community/repl)) — keeps mathlib loaded in memory, JSON stdin/stdout, fast round-trips. **Chosen as the default** for this project — good fit for "no training, just loop + retry" scope.
- **LeanDojo-v2** ([lean-dojo/LeanDojo-v2](https://github.com/lean-dojo/LeanDojo-v2)) — fuller framework, tactic-state extraction, tracing. More setup overhead; aimed more at RL/training pipelines. Worth revisiting if the project later grows into training.
- **Pantograph** ([leanprover/Pantograph](https://github.com/leanprover/Pantograph)) — another machine-to-machine Lean 4 interface, built for programmatic proof search.
Decision: start with the Lean REPL. Swap later if it doesn't fit.
 
## miniF2F Lean 4 forks
- [google-deepmind/miniF2F](https://github.com/google-deepmind/miniF2F) — fork of openai/miniF2F, corrected formalizations, appears actively maintained. Leading candidate.
- [facebookresearch/minif2f](https://github.com/facebookresearch/minif2f) — updated version with fixes + informal statements/solutions.
- [yangky11/miniF2F-lean4](https://github.com/yangky11/miniF2F-lean4), [rahul3613/miniF2F-lean4](https://github.com/rahul3613/miniF2F-lean4) — community ports.
- Note: [miniF2F-Lean Revisited](https://arxiv.org/pdf/2511.03108) (OpenReview: https://openreview.net/forum?id=KtaHv0YUyh) documents known limitations in the benchmark — worth a skim before locking in a fork + toolchain version.
No fork chosen yet.
 
## Open decisions (not yet made)
- Which LLM API generates candidate proof steps (closed API vs open-weight model) — deferred.
- Which miniF2F fork + matching Lean/mathlib toolchain version to pin.
- Retry loop design specifics: max retries, what error context to feed back, whether to pass partial progress (e.g. remaining `sorry`s) back to the model, stopping criteria.
- Repo structure (Lean project layout, prompts, orchestration scripts, results/logging).
## Next steps (none started yet)
- Repo + Lean project scaffolding (elan/lake init with mathlib dependency) in the LEAN_AI folder.
- Fetch a miniF2F Lean 4 fork into the project.
- Write the orchestration loop skeleton once the LLM provider is picked.
 
