# Run summary — `2026-09-21_valid_600s_partial`

Status: **partial — 25/256 theorems evaluated**.

| Metric | Value |
|---|---|
| Theorems evaluated | 25 / 256 |
| Solved (Lean-verified) | **2 / 25 (8.0%)** |
| Solved on the first attempt (pass@1) | 1 / 25 (4.0%) |
| Solved only after Lean-feedback retries | 1 |
| Model attempts (total / median per theorem) | 378 / 16 |
| Median time per attempt (generation + Lean check) | 38 s |
| Median time to a verified proof | 4 s |

## By problem source

| Source | Solved | Evaluated | Rate |
|---|---|---|---|
| MATH — algebra | 2 | 4 | 50.0% |
| MATH — number theory | 0 | 8 | 0.0% |
| AMC 12 | 0 | 6 | 0.0% |
| AIME | 0 | 2 | 0.0% |
| IMO | 0 | 4 | 0.0% |
| Custom (algebra / number theory / induction) | 0 | 1 | 0.0% |

## Outcome of individual attempts

| Outcome | Attempts | Share |
|---|---|---|
| Rejected by Lean | 376 | 99.5% |
| Verified proof | 2 | 0.5% |

## Why Lean rejected attempts

Share of rejected attempts containing at least one error of each kind (an attempt can fall in several).

| Error kind | Rejected attempts | Share |
|---|---|---|
| Tactic failed / goals left open | 324 | 86.2% |
| Syntax error (often Lean 3 / old Mathlib syntax) | 207 | 55.1% |
| Other | 120 | 31.9% |
| Hallucinated name (unknown identifier / constant / field) | 108 | 28.7% |
| Type error | 74 | 19.7% |

## Solved theorems

- `mathd_algebra_182` (2 s)
- `mathd_algebra_462` (5 s)

