# Run summary — `2026-10-03_smoke_test`

Status: complete.

| Metric | Value |
|---|---|
| Theorems evaluated | 5 / 5 |
| Solved (Lean-verified) | **1 / 5 (20.0%)** |
| Solved on the first attempt (pass@1) | 1 / 5 (20.0%) |
| Solved only after Lean-feedback retries | 0 |
| Model attempts (total / median per theorem) | 11 / 2 |
| Median time per attempt (generation + Lean check) | 37 s |
| Median time to a verified proof | 6 s |

## By problem source

| Source | Solved | Evaluated | Rate |
|---|---|---|---|
| MATH — algebra | 1 | 1 | 100.0% |
| AMC 12 | 0 | 3 | 0.0% |
| AIME | 0 | 1 | 0.0% |

## Outcome of individual attempts

| Outcome | Attempts | Share |
|---|---|---|
| Rejected by Lean | 9 | 81.8% |
| Verified proof | 1 | 9.1% |
| No complete ```lean4 block | 1 | 9.1% |

## Why Lean rejected attempts

Share of rejected attempts containing at least one error of each kind (an attempt can fall in several).

| Error kind | Rejected attempts | Share |
|---|---|---|
| Tactic failed / goals left open | 9 | 100.0% |
| Syntax error (often Lean 3 / old Mathlib syntax) | 7 | 77.8% |
| Type error | 2 | 22.2% |
| Hallucinated name (unknown identifier / constant / field) | 1 | 11.1% |

## Solved theorems

- `mathd_algebra_182` (6 s)

