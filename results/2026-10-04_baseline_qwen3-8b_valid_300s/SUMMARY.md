# Run summary — `2026-10-04_baseline_qwen3-8b_valid_300s`

Status: **partial — 186/256 theorems evaluated**.

| Metric | Value |
|---|---|
| Theorems evaluated | 186 / 256 |
| Solved (Lean-verified) | **12 / 186 (6.5%)** |
| Solved on the first attempt (pass@1) | 7 / 186 (3.8%) |
| Solved only after Lean-feedback retries | 5 |
| Model attempts (total / median per theorem) | 1885 / 10 |
| Median time per attempt (generation + Lean check) | 26 s |
| Median time to a verified proof | 5 s |

## By problem source

| Source | Solved | Evaluated | Rate |
|---|---|---|---|
| MATH — algebra | 4 | 52 | 7.7% |
| MATH — number theory | 5 | 52 | 9.6% |
| AMC 12 | 1 | 36 | 2.8% |
| AIME | 0 | 12 | 0.0% |
| IMO | 0 | 11 | 0.0% |
| Custom (algebra / number theory / induction) | 2 | 23 | 8.7% |

## Outcome of individual attempts

| Outcome | Attempts | Share |
|---|---|---|
| Rejected by Lean | 1852 | 98.2% |
| No complete ```lean4 block | 13 | 0.7% |
| Verified proof | 12 | 0.6% |
| Contains `sorry` | 8 | 0.4% |

## Why Lean rejected attempts

Share of rejected attempts containing at least one error of each kind (an attempt can fall in several).

| Error kind | Rejected attempts | Share |
|---|---|---|
| Tactic failed / goals left open | 1557 | 84.1% |
| Syntax error (often Lean 3 / old Mathlib syntax) | 964 | 52.1% |
| Hallucinated name (unknown identifier / constant / field) | 699 | 37.7% |
| Type error | 397 | 21.4% |
| Other | 224 | 12.1% |

## Solved theorems

- `algebra_2rootspoly_apatapbeq2asqp2ab` (3 s)
- `algebra_sqineq_4bap1lt4bsqpap1sq` (34 s)
- `amc12a_2009_p2` (2 s)
- `mathd_algebra_182` (3 s)
- `mathd_algebra_245` (17 s)
- `mathd_algebra_48` (6 s)
- `mathd_algebra_568` (7 s)
- `mathd_numbertheory_101` (59 s)
- `mathd_numbertheory_132` (2 s)
- `mathd_numbertheory_169` (10 s)
- `mathd_numbertheory_188` (2 s)
- `mathd_numbertheory_81` (2 s)

