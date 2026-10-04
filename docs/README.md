# Documentation

Engineering notes written while the project was being built. They record the actual
decisions, including the mistakes and how they were found.

| Document | What it is |
|---|---|
| [`design_review_2026_09_20.md`](design_review_2026_09_20.md) | **Adversarial review** of the evaluation pipeline. It checks every design decision against the real code and the Lean REPL source, then lists soundness, reliability, compute and evaluation-design issues (A1–F) and how to fix each one. The identity check and the harness-error guard came out of it. |
| [`project_plan.md`](project_plan.md) | Roadmap and phase-level decisions: base model choice, compute budget, phases 1–3. |
| [`context.md`](context.md) | Full implementation journal: Lean REPL protocol quirks, parser edge cases, every bug hit and how it was found. Long; read the section you need. |
| [`changelog.md`](changelog.md) | Session-by-session record of code changes. |
| [`setup_notes.md`](setup_notes.md) | Initial research: choice of Lean interface (REPL vs LeanDojo vs Pantograph) and of the miniF2F fork. |

The notes are kept as they were written. A few sections describe states of the code that
have since changed. Where they disagree with the code, the code is correct.
