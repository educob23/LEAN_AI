import parser
from mlx_lm import load, generate

model, tokenizer = load("mlx-community/Qwen3-8B-4bit")

theorems = parser.extract_theorems("/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Valid_parser.lean")
template = theorems["amc12a_2019_p21"]  # reusing the one you already confirmed works against the real REPL

instruction = (
    "You are proving a theorem in Lean 4 using Mathlib. "
    "Complete the following theorem by replacing `sorry` with a valid Lean 4 proof. "
    "Output only the complete Lean code, nothing else.\n\n"
    + template
)

messages = [{"role": "user", "content": instruction}]
prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True, enable_thinking = False)  # thinking left ON by default

text = generate(model, tokenizer, prompt=prompt, verbose=False, max_tokens=12000)
print(text)