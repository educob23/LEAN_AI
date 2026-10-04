"""parser.py on a small file that reproduces the edge cases found in miniF2F."""
import shutil
from pathlib import Path

import pytest

import parser

FIXTURE = Path(__file__).parent / "fixtures" / "Sample.lean"


@pytest.fixture
def parsed_path(tmp_path):
    src = tmp_path / "Sample.lean"
    shutil.copy(FIXTURE, src)
    parser.drop_comments(str(src), "Sample")
    out = tmp_path / "Sample_parser.lean"
    assert out.exists()
    return out


def test_drop_comments_removes_every_comment(parsed_path):
    text = parsed_path.read_text()
    assert "/-" not in text and "-/" not in text and "--" not in text
    assert "one-line docstring" not in text and "blank line" not in text
    assert "author-credits" not in text and "trailing comment" not in text
    assert text.count("theorem ") == 4


def test_treat_header(parsed_path):
    imports, opens = parser.treat_header(str(parsed_path))
    assert imports == ["MiniF2F.ProblemImports"]
    assert opens == {"Real": 1, "Nat": 1}


def test_extract_theorems_names(parsed_path):
    theorems = parser.extract_theorems(str(parsed_path))
    assert list(theorems) == [
        "first_problem",
        "algebra.variants.dotted_name",
        "no_docstring",
        "already_proved",
    ]


def test_templates_are_verbatim_and_end_in_sorry(parsed_path):
    theorems = parser.extract_theorems(str(parsed_path))
    for name in ["first_problem", "algebra.variants.dotted_name", "no_docstring"]:
        template = theorems[name]
        assert template.lstrip().startswith(f"theorem {name}")
        assert template.rstrip().endswith("sorry")
        assert template.count("sorry") == 1
    # multi-line statement kept with its original line break
    assert "(h₀ : a = b) :\n    a + 0 = b := by" in theorems["algebra.variants.dotted_name"]
    # answer(...) wrapper is kept inline, not masked
    assert "answer(1)" in theorems["first_problem"]


def test_last_theorem_without_sorry_is_kept_separate(parsed_path):
    theorems = parser.extract_theorems(str(parsed_path))
    assert "simp" in theorems["already_proved"]
    assert "already_proved" not in theorems["no_docstring"]
