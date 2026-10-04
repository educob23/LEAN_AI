import MiniF2F.ProblemImports

open scoped Real
open scoped Nat

/-
  A plain block comment at the top of the file,
  like the author-credits block in miniF2F's Valid.lean.
-/

/-- A one-line docstring. -/
theorem first_problem (x : ℝ) (h₀ : x + 1 = 2) : x = answer(1) := by
  sorry

/-- A multi-paragraph docstring.

It even contains a blank line, and the words theorem and sorry. -/
theorem algebra.variants.dotted_name (a b : ℕ) (h₀ : a = b) :
    a + 0 = b := by
  sorry


theorem no_docstring (n : ℕ) : n = n := by -- a trailing comment
  sorry

/-- The last problem has a real proof instead of `sorry`, like two entries of Test.lean. -/
theorem already_proved (n : ℕ) : n + 0 = n := by
  simp
