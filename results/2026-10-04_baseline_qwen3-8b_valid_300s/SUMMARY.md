# Run summary — `2026-10-04_baseline_qwen3-8b_valid_300s`

Status: complete.

| Metric | Value |
|---|---|
| Theorems evaluated | 256 / 256 |
| Solved (Lean-verified) | **17 / 256 (6.6%)** |
| Solved on the first attempt (pass@1) | 9 / 256 (3.5%) |
| Solved only after Lean-feedback retries | 8 |
| Model attempts (total / median per theorem) | 2656 / 10 |
| Median time per attempt (generation + Lean check) | 25 s |
| Median time to a verified proof | 6 s |

## By problem source

| Source | Solved | Evaluated | Rate |
|---|---|---|---|
| MATH — algebra | 6 | 71 | 8.5% |
| MATH — number theory | 7 | 67 | 10.4% |
| AMC 12 | 1 | 49 | 2.0% |
| AIME | 0 | 15 | 0.0% |
| IMO | 0 | 20 | 0.0% |
| Custom (algebra / number theory / induction) | 3 | 34 | 8.8% |

## Outcome of individual attempts

| Outcome | Attempts | Share |
|---|---|---|
| Rejected by Lean | 2606 | 98.1% |
| No complete ```lean4 block | 22 | 0.8% |
| Verified proof | 17 | 0.6% |
| Contains `sorry` | 11 | 0.4% |

## Why Lean rejected attempts

Share of rejected attempts containing at least one error of each kind (an attempt can fall in several).

| Error kind | Rejected attempts | Share |
|---|---|---|
| Tactic failed / goals left open | 2208 | 84.7% |
| Syntax error (often Lean 3 / old Mathlib syntax) | 1341 | 51.5% |
| Hallucinated name (unknown identifier / constant / field) | 913 | 35.0% |
| Type error | 502 | 19.3% |
| Other | 340 | 13.0% |

## Solved theorems

- `algebra_2rootspoly_apatapbeq2asqp2ab` (3 s)
- `algebra_manipexpr_2erprsqpesqeqnrpnesq` (7 s)
- `algebra_sqineq_4bap1lt4bsqpap1sq` (34 s)
- `amc12a_2009_p2` (2 s)
- `mathd_algebra_182` (3 s)
- `mathd_algebra_245` (17 s)
- `mathd_algebra_48` (6 s)
- `mathd_algebra_568` (7 s)
- `mathd_algebra_616` (104 s)
- `mathd_algebra_89` (4 s)
- `mathd_numbertheory_101` (59 s)
- `mathd_numbertheory_132` (2 s)
- `mathd_numbertheory_169` (10 s)
- `mathd_numbertheory_188` (2 s)
- `mathd_numbertheory_202` (20 s)
- `mathd_numbertheory_81` (2 s)
- `mathd_numbertheory_961` (3 s)

