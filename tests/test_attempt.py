"""
retry_loop.attempt with the model and the REPL replaced by fakes.

What matters here is the soundness check: the command sent to Lean must contain the
model's proof *and* an identity check built from the trusted template, so that a
model cannot pass by proving an easier statement under the same name.
"""
import retry_loop

TEMPLATE = "theorem demo (n : ℕ) (h₀ : 0 < n) :\n    n + 0 = n := by\n  sorry\n"


class FakeTokenizer:
    def apply_chat_template(self, messages, **kwargs):
        return "prompt"


class FakeRepl:
    def __init__(self, answer):
        self.answer = answer
        self.sent = None

    def write_proof(self, cmd):
        self.sent = cmd
        return self.answer

    def check(self, answer):
        return 1 if answer == {"env": 1} else -1


def run(monkeypatch, model_output, answer=None):
    monkeypatch.setattr(retry_loop, "generate", lambda *a, **k: model_output)
    repl = FakeRepl(answer or {"env": 1})
    result = retry_loop.attempt([], TEMPLATE, repl, None, FakeTokenizer(), enable_thinking=False)
    return result, repl


def test_identity_check_is_appended(monkeypatch):
    proof = "theorem demo (n : ℕ) (h₀ : 0 < n) : n + 0 = n := by simp"
    (check, extracted, raw, answer), repl = run(monkeypatch, f"```lean4\n{proof}\n```")
    assert check == 1
    assert extracted.strip() == proof
    # model proof first, then the check built from the trusted template
    assert repl.sent.index(proof) < repl.sent.index("example")
    assert "theorem demo" not in repl.sent.split("example", 1)[1]
    assert "apply demo <;> assumption" in repl.sent
    assert repl.sent.count("set_option maxHeartbeats 400000 in") == 2


def test_no_code_block_skips_lean(monkeypatch):
    (check, proof, raw, answer), repl = run(monkeypatch, "I give up.")
    assert (check, proof, answer) == (None, None, None)
    assert raw == "I give up."
    assert repl.sent is None
