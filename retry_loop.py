import wrapper
import parser
import time
import json

from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler, make_logits_processors

def extract_proof(text):
    """
        Auxiliar function that extracts only the Lean proof from the model answer so that it can be given directly to a LEAN environnment
        If the model never gave the proof returns None, if it did but the answer got sliced returns None (possible optimisation in the future)
    """
    # La preuve LEAN commence après "```lean4" et se ferme avec "```" 
    # On récupère donc les index de début et fin de la preuve
    start = text.rfind("```lean4")
    if start == -1:
            return None
    end = text.find("```", start+8)
    if end == -1:
        return None
    else:
        return text[start+8 : end]


def attempt(messages, template, Repl, model, tokenizer, enable_thinking, max_tokens = 12000, verbose = False ):
    """
        Runs one loop based on previous context, runs the model to generate a proof, extracts it and checks the answer on a Lean environement
            params :

            returns :
                check : if the proof worked or not
                proof : the proof the model built
                raw_text : the models raw response
                answer : Lean's answer to the proof
    """
    prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True, enable_thinking = enable_thinking)

    # We use Qwen's own commended values for thinking mode
    if enable_thinking:
        sampler = make_sampler(temp=0.6, top_p=0.95, top_k=20, min_p=0.0)
    else:
        sampler = make_sampler(temp=0.7, top_p=0.8, top_k=20, min_p=0.0)

    logits_processors = make_logits_processors(repetition_penalty=1.1, repetition_context_size=64)

    # Model answer
    # We use verbose = False, can be changed to True for debugging
    raw_text = generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens, verbose = False, sampler=sampler, logits_processors=logits_processors)

    ## we extract the Lean proof from the model answer
    proof = extract_proof(raw_text)
    if proof == None:
        print("Model dind't gave a complete answer!!")
        return None, None, raw_text, None
    
    # we check that proof on Lean

    # we need to add an extra check to make sure the model doesn't bypass the proof of the thm
    thm_name = template.split()[1]
    check_cmd = (
        template
        .replace(f"theorem {thm_name}", "example", 1)
        .replace("sorry", f"apply {thm_name} <;> assumption", 1)
    )
    # and we add a heartbeat limit for when it will run on Lean
    bounded_proof = f"set_option maxHeartbeats 400000 in\n{proof}"
    bounded_check_cmd = f"set_option maxHeartbeats 400000 in\n{check_cmd}"
    full_cmd = bounded_proof + "\n\n" + bounded_check_cmd

    try:
        answer = Repl.write_proof(full_cmd)
    except RuntimeError as e:
        # wrapper.py gave up: max_consecutive_timeouts exceeded, meaning the
        # environment reload itself is stuck/broken, not just one bad proof.
        # Get a clean REPL ready for whatever comes next, and abandon this
        # theorem rather than retrying against what was just broken.
        if verbose:
            print(f"REPL gave up on this theorem: {e}")
        Repl.force_restart()
        return "repl_gave_up", proof, raw_text, {"error": str(e)}

    if verbose:
        print(answer)
    check = Repl.check(answer)

    return check, proof, raw_text, answer


#######
def log_attempt(logfile, theorem, attempt_idx, raw_text, proof, answer, check, elapsed):
    record = {"theorem": theorem, "attempt": attempt_idx, "raw_text": raw_text,
              "proof": proof, "answer": answer, "check": check,
              "elapsed_s": elapsed, "ts": time.time()}
    with open(logfile, "a") as f:
        f.write(json.dumps(record) + "\n")
#######

def full_attempt(messages, thm, thm_name, Repl, model, tokenizer, enable_thinking, max_tokens, verbose, attempt_idx, logfile):
    """ attempts + hard log of the attempt """
    t0 = time.monotonic()
    check, proof, raw_text, answer = attempt(messages, thm, Repl, model, tokenizer, enable_thinking, max_tokens, verbose)
    elapsed = time.monotonic() - t0
    log_attempt(logfile, thm_name, attempt_idx, raw_text, proof, answer, check, elapsed)
    return check, proof, raw_text, answer


def loop(thm, Repl, model, tokenizer, enable_thinking, max_tokens = 12000, verbose = False, time_budget_seconds = 600, logfile = "attempts.jsonl"):
    """ 
        
            params :
                
            returns :

    """
    start = time.monotonic()
    thm_name = thm.split()[1]
    attempt_idx = 0

    # The first message given to the model :
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
        "code block, with nothing else inside that block. \n"
        "Do not include any import or open statements, the environment already has everything needed. \n"
    )
    messages = [{"role": "user", "content": instruction}]

    # we run an attempt
    check, proof, raw_text, answer = full_attempt(messages, thm, thm_name, Repl, model, tokenizer, enable_thinking, max_tokens, verbose, attempt_idx, logfile)
    attempt_idx += 1

    while time.monotonic() - start < time_budget_seconds:
        if check == 1:
            # proof is correct!
            return check, proof
        
        if check == "repl_gave_up":
            # Already restarted inside attempt(); don't keep retrying against
            # what was just a broken environment -- give up on this theorem only.
            return check, proof

        # we give the model it's previous thougth process
        messages.append({"role": "assistant", "content": raw_text})

        if check == "harness_error":
            follow_up = (
                "There was a problem checking that answer. Please try again with "
                "a complete Lean 4 proof.\n"
            )

        elif check == "timeout":
            follow_up = (
                "That attempt took too long and was interrupted (not necessarily a "
                "problem with your proof). Please try again.\n"
            )

        elif check == None:
            # model wasn't able to give an answer
            follow_up = (
                "You didn't finish: no complete ```lean4 code block was found in your "
                "last answer.\n\n"
                "Give the complete theorem (statement and proof) inside a single "
                "```lean4 code block, with nothing else inside it.\n"
            )
        elif check == 0:
            # there's a sorry in the answer. redo?
            follow_up = (
                "Your proof still contains `sorry` — it isn't complete.\n\n"
                f"```lean4\n{proof}```\n\n"
                "Replace the remaining `sorry` with a real proof.\n"
            )
        else:
            # proof is incorrect - try again
            errors = answer["messages"]
            follow_up = (
                "Lean rejected this proof:\n\n"
                f"```lean4\n{proof}```\n\n"
                f"Lean's error:\n{errors}\n\n"
                "Fix the proof and try again.\n"
            )

        messages.append({"role": "user", "content": follow_up})
        check, proof, raw_text, answer = full_attempt(messages, thm, thm_name, Repl, model, tokenizer, enable_thinking, max_tokens, verbose, attempt_idx, logfile)
        attempt_idx += 1

    return "timed_out", proof



if __name__ == "__main__":
    path_to_Valid = "/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Valid.lean"
    path_to_Valid_parsed = "/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Valid_parser.lean"

    parser.drop_comments(path_to_Valid, "Valid")
    imports, opens = parser.treat_header(path_to_Valid_parsed)
    theorems = parser.extract_theorems(path_to_Valid_parsed)

    Repl = wrapper.LEANRepl()
    Repl.import_project(imports, opens)

    model, tokenizer = load("mlx-community/Qwen3-8B-4bit")

    print(loop(theorems['amc12a_2019_p21'], Repl, model, tokenizer, enable_thinking = False, max_tokens = 5000, verbose = True))

    Repl.close()