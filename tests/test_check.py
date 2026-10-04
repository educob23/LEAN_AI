"""wrapper.LEANRepl.check: map a raw REPL response to a verdict, without a Lean process."""
import pytest

import wrapper


@pytest.fixture
def repl():
    # check() never touches the subprocess, so skip __init__ (which would spawn Lean)
    return object.__new__(wrapper.LEANRepl)


def test_clean_response_passes(repl):
    assert repl.check({"env": 3}) == 1


def test_warnings_only_pass(repl):
    answer = {"env": 3, "messages": [{"severity": "warning", "data": "unused variable"}]}
    assert repl.check(answer) == 1


def test_error_fails(repl):
    answer = {"env": 3, "messages": [{"severity": "error", "data": "unsolved goals"}]}
    assert repl.check(answer) == -1


def test_sorry_is_not_a_pass(repl):
    assert repl.check({"env": 3, "sorries": [{"goal": "⊢ False"}]}) == 0
    answer = {"env": 3, "messages": [{"severity": "warning", "data": "declaration uses 'sorry'"}],
              "sorries": [{"goal": "⊢ False"}]}
    assert repl.check(answer) == 0


def test_repl_level_failure_is_not_scored_as_a_pass(repl):
    # REPL-level errors use a singular "message" field and carry no "env"
    assert repl.check({"message": "Unknown environment."}) == "harness_error"


def test_timeout(repl):
    assert repl.check({"timeout": True}) == "timeout"
