LLM-assisted Lean proof generation

A system where an LLM proposes candidate proof steps for math problems, and Lean's compiler verifies them — failing proofs get fed back to the LLM to retry (a self-correcting loop)

Scope: use an existing LLM API, a small benchmark set of problems (miniF2F-style), Lean as the verifier. No training required — the engineering is in the loop, the prompting, and the retry logic
