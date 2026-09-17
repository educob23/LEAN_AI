import wrapper
import parser
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler, make_logits_processors

def loop(thm, imports, opens, enable_thinking, max_tokens):
    """ 
        Sends a theorem to the model using a pre-buuilt prompt and checks it in a Lean environnement that was built with imports and opens
            params :
                thm :
                imports :
                opens :
                enable_thinking :
                max_tokens : 
            returns :

    """
    ## ??
    model, tokenizer = load("mlx-community/Qwen3-8B-4bit")

    # The message given to the model :
    # We're using the same prompt DeepSeek-Prover-V2 and Goedel-Prover-V2 use on their model
    instruction = (
        "Complete the following Lean 4 theorem using Mathlib.\n\n"
        "```lean4\n"
        f"{thm}"
        "```\n\n"
        "Before writing the proof, briefly outline your proof strategy: the key lemmas, "
        "intermediate steps, or tactics you plan to use. Then give the complete Lean 4 code.\n\n"
        "Rules:\n"
        "- Replace `sorry` with a real proof. If you get stuck, leave `sorry` only where you "
        "truly cannot make progress — don't keep searching indefinitely on one step.\n"
        "- Prefer tactics that don't depend on recalling an exact lemma name when they apply "
        "(`ring`, `field_simp`, `norm_num`, `nlinarith`, `decide`, `simp`) over long chains of "
        "manually named `rw`/`have` steps.\n"
        "- Give the final, complete theorem (statement and proof) inside a single ```lean4 "
        "code block, with nothing else inside that block.\n"
    )
    messages = [{"role": "user", "content": instruction}]
    prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True, enable_thinking = enable_thinking)

    # We use Qwen's own commended values for thinking mode 
    sampler = make_sampler(temp=0.6, top_p=0.95, top_k=20, min_p=0.0)  # if we use enable_thinking = True
    #sampler = make_sampler(temp=0.7, top_p=0.8, top_k=20, min_p=0.0).  # if we use enable_thinking = False
    logits_processors = make_logits_processors(repetition_penalty=1.1, repetition_context_size=64)

    # Model answer
    # We use verbose = False, can be changed to True for debugging
    text = generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens, verbose = False, sampler=sampler, logits_processors=logits_processors)

    ## we check the answer on the LEAN environement
    print("building LEAN environement")
    Repl = wrapper.LEANRepl()
    Repl.import_project(imports, opens)
    answer = Repl.write_proof(text)
    check = Repl.check(answer)

    Repl.close()
    return check


path_to_Valid = "/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Valid.lean"
path_to_Valid_parsed = "/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Valid_parser.lean"

parser.drop_comments(path_to_Valid, "Valid")
imports, opens = parser.treat_header(path_to_Valid_parsed)
theorems = parser.extract_theorems(path_to_Valid_parsed)

print(loop(theorems['amc12a_2019_p21'], imports, opens, enable_thinking = True, max_tokens = 12000))
