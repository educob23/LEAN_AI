"""retry_loop.extract_proof: pull the final ```lean4 block out of a model answer."""
from retry_loop import extract_proof


def test_single_block():
    text = "Plan: use norm_num.\n```lean4\ntheorem t : 1 + 1 = 2 := by norm_num\n```\nDone."
    assert extract_proof(text) == "\ntheorem t : 1 + 1 = 2 := by norm_num\n"


def test_takes_the_last_block():
    text = (
        "<think>draft:\n```lean4\ntheorem t : 1 = 1 := by sorry\n```\n</think>\n"
        "Final:\n```lean4\ntheorem t : 1 = 1 := rfl\n```"
    )
    assert extract_proof(text) == "\ntheorem t : 1 = 1 := rfl\n"


def test_no_block_returns_none():
    assert extract_proof("I could not find a proof.") is None


def test_unclosed_block_returns_none():
    # the model ran out of tokens in the middle of its answer
    assert extract_proof("```lean4\ntheorem t : 1 = 1 := by\n  simp") is None
