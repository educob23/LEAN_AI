# Documentation

| Document | What it is |
|---|---|
| [`design_review_2026_09_20.md`](design_review_2026_09_20.md) | **Adversarial review** of the evaluation pipeline. It checks every design decision against the real code and the Lean REPL source, then lists soundness, reliability, compute and evaluation-design issues (A1–F) and how to fix each one. The identity check and the harness-error guard came out of it. |
| [`setup_notes.md`](setup_notes.md) | Initial research: choice of Lean interface (REPL vs LeanDojo vs Pantograph) and of the miniF2F fork. |

The roadmap and the decision log are in [`ROADMAP.md`](../ROADMAP.md); archived runs are in
[`results/`](../results/).

The design review cites my private working notes (`context.md`, `project-plan.md`), which
are not part of this repository. Some sections describe states of the code that have since
changed; where they disagree with the code, the code is correct.
