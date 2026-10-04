# Notebooks and early experiments

Exploration kept for reference. Nothing in the pipeline imports from here.

| File | Purpose |
|---|---|
| `prototype_pipeline.ipynb` | First interactive prototype of the parse → generate → check pipeline. |
| `validation_checks.ipynb` | Checks run against the real model and REPL: (1) Qwen3's chat template strips earlier `<think>` blocks from multi-turn history; (2) the identity check accepts a correct proof and rejects a renamed trivial statement; (3) a REPL-level error is reported as a harness error. |
| `first_generation.py` | The very first generation call to Qwen3-8B. |
| `sample_model_output.lean` | An early raw model answer, kept as an example of typical failure modes. |

Run notebooks with the repository root as the working directory so that `parser`,
`wrapper` and `retry_loop` can be imported.
