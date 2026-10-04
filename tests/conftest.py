"""
Test setup.

The tests run offline: no Lean toolchain, no model weights, no Apple Silicon.
`mlx_lm` is only importable on macOS/Apple Silicon, so a minimal stub is
registered before `retry_loop` is imported. Generation itself is never
exercised here -- tests that need a model response patch `retry_loop.generate`.
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if "mlx_lm" not in sys.modules:
    try:
        import mlx_lm  # noqa: F401  (real package available, e.g. on a Mac)
    except ImportError:
        mlx_lm = types.ModuleType("mlx_lm")
        mlx_lm.load = lambda *a, **k: (None, None)
        mlx_lm.generate = lambda *a, **k: ""
        sample_utils = types.ModuleType("mlx_lm.sample_utils")
        sample_utils.make_sampler = lambda **k: None
        sample_utils.make_logits_processors = lambda **k: None
        mlx_lm.sample_utils = sample_utils
        sys.modules["mlx_lm"] = mlx_lm
        sys.modules["mlx_lm.sample_utils"] = sample_utils
