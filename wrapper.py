import subprocess
import json
import parser
import threading
import queue


class LEANRepl :

    def __init__(self) :
        """ 
            Starts the LEANRepfl as a subprocess. Once import_project is called proofs can be verified on the subprocess
        """
        self._imports = None
        self._opens = None
        self.restart_count = 0
        self._start_process()
        self.base_env = None

    def _start_process(self):
        """ (re)spawns the REPL subprocess, used by __init__ and by a timeout restart """
        self.proc = subprocess.Popen(["lake", "env", "../repl_minif2f/.lake/build/bin/repl"],
            cwd="/Users/eduardo/Desktop/LEAN_AI/miniF2F", stdin=subprocess.PIPE, stdout=subprocess.PIPE, text = True)

    def _read_response(self):
        """  """
        lines = []
        line = self.proc.stdout.readline()
        while(line != "\n") :
            if(line == "") :
                print("error on LEAN answer!!")
                break
            lines.append(line)  # the JSON response
            line = self.proc.stdout.readline()
        return json.loads("".join(lines))



            
    def send(self, message, timeout=120):
        #writing of the message
        self.proc.stdin.write(message)
        self.proc.stdin.flush()

        q = queue.Queue()
        def _worker():
            try:
                q.put(("ok", self._read_response()))
            except Exception as e:
                q.put(("error", e))

        threading.Thread(target=_worker, daemon=True).start()

        try:
            status, result = q.get(timeout=timeout)
        except queue.Empty:
            self._restart()
            return {"timeout": True}

        if status == "error":
            raise result
        return result

    def _restart(self):
        """  """
        self.restart_count += 1
        try:
            self.proc.kill()
        except Exception:
            pass
        self._start_process()
        if self._imports is not None:
            self.import_project(self._imports, self._opens)


    def write_proof(self, cmd):
        """
            writes the proof cmd inside the LEAN environement and returns the LEAN evaluation
            cmd is a string with the proof
        """
        #checking import_project was run
        if(self.base_env == None):
            raise RuntimeError("didn't calles import_project before write_proof")
        #sending the proof and returning LEAN answer
        return self.send(json.dumps({"cmd": cmd, "env": self.base_env}) + "\n\n")
        

    def import_project(self, imports, opens):
        """
            Imports all the needed imports, needed for every proof and saves time by doing it just once
            params :
              imports : a tab with all the files to import
              opens : a dic with all the things to open in label and 0 if not scopped 1 if yes 
        """
        self._imports = imports
        self._opens = opens
        
        json_txt = ""
        for imp in imports :
            json_txt = json_txt + "import " + imp + "\n"
        for open in opens :
            if opens[open] :
                json_txt = json_txt + "open " + "scoped " + open + "\n"
            else:
                json_txt = json_txt + "open " + open + "\n"

        response = self.send(json.dumps({"cmd": json_txt})+ "\n\n")
        self.base_env = response["env"]
        return response


    def close(self):
        """
            closes the subprocess, to be done after every LEANRepl class served it use
        """
        self.proc.stdin.close()
        try:
            self.proc.wait(5)
        except subprocess.TimeoutExpired:
            self.proc.kill()

    def check(self, answer):
        """
            checks if LEAN considers the proof correct,incorrect or if there's the use of sorry in the proof

            param:
                answer: the LEAN evaluation returned by write_proof((self, cmd))

            returns:
                1 if the proof is correct, 0 if it uses sorry, -1 if there's an error
        """
        if answer.get("timeout"):
            return "timeout"
        
        if "env" not in answer:
        # a normal response always has an "env" id - if it's missing, something went bad
            return "harness_error"

        ######## what if there's warnings like unused variable but the prrof is correct? To check
        if("messages" not in answer and "sorries" not in answer):
            return 1
        if("messages" in answer):
            if(any(m["severity"] == "error" for m in answer["messages"])):
                return -1
            elif("sorries" in answer):
                return 0
            else:
                return 1
        if("sorries" in answer):
            return 0
        
        raise RuntimeError(f"No case for {answer}")

if __name__ == "__main__":

    path_to_Valid = "/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Valid.lean"
    path_to_Valid_parsed = "/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Valid_parser.lean"

    path_to_Test = "/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Test.lean"
    path_to_Test_parsed = "/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Test_parser.lean"

    ##extraction from files
    parser.drop_comments(path_to_Valid, "Valid")
    imports_Valid, opens_Valid = parser.treat_header(path_to_Valid_parsed)
    theorems_Valid = parser.extract_theorems(path_to_Valid_parsed)

    parser.drop_comments(path_to_Test, "Test")
    imports_Test, opens_Test = parser.treat_header(path_to_Test_parsed)
    theorems_Test = parser.extract_theorems(path_to_Test_parsed)

    #creation of REPL_Valid
    Repl_Valid = LEANRepl()
    Repl_Valid.import_project(imports_Valid, opens_Valid)

    #creation of REPL_Test
    Repl_Test = LEANRepl()
    Repl_Test.import_project(imports_Test, opens_Test)

    #check of one of the theorems from valid
    answer1 = Repl_Valid.write_proof(theorems_Valid['amc12a_2019_p21'])
    check1 = Repl_Valid.check(answer1)

    if(check1 != 0):
        print(" Error in the Validation Thm!!")
    else:
        print("runned correctly")

    #check of one of the theorems from Test
    answer2 = Repl_Test.write_proof(theorems_Test['mathd_algebra_478'])
    check2 = Repl_Test.check(answer2)

    if(check2 != 0):
        print(" Error in the Validation Thm!!")
    else:
        print("runned correctly")

    proof = """theorem amc12a_2019_p21 (z : ℂ) (h₀ : z = (1 + Complex.I) / Real.sqrt 2) :
        (∑ k ∈ Finset.Icc 1 12, z ^ k ^ 2) * ∑ k ∈ Finset.Icc 1 12, 1 / z ^ k ^ 2 = answer(36) := by
    let z' := (1 + Complex.I) / Real.sqrt 2
    have h : z = z' := h₀
    let z₂ := z ^ 2
    let z₂' := z' ^ 2
    have h₂ : z₂ = z₂' := by rw [h, pow_inj]
    have h₂' : z₂' = (1 + Complex.I) ^ 2 / (Real.sqrt 2) ^ 2 := by
        rw [pow_mul, pow_two, Real.sqrt_two_pow_two]
        simp [Real.sqrt_two_pow_two]
    have h₂'' : z₂' = (1 + 2 * Complex.I - 1) / 2 := by
        simp [Complex.I, Complex.add, Complex.pow_two, Complex.mul, Complex.neg]
    have h₂''' : z₂' = Complex.I := by simp [h₂', Complex.I]
    have h₂'''' : z₂ = Complex.I := by rw [h₂, h₂''', eq_self]
    let s := ∑ k ∈ Finset.Icc 1 12, z ^ k ^ 2
    let t := ∑ k ∈ Finset.Icc 1 12, 1 / z ^ k ^ 2
    have s_eq : s = ∑ k ∈ Finset.Icc 1 12, Complex.I ^ k := by
        rw [h₂''', pow_one, pow_pow, pow_one, pow_one]
        simp [Finset.Icc, Finset.sum_const, Finset.sum_eq_zero, Finset.sum_eq_zero]
    have t_eq : t = ∑ k ∈ Finset.Icc 1 12, 1 / Complex.I ^ k := by
        rw [h₂''', pow_one, pow_pow, pow_one, pow_one]
        simp [Finset.Icc, Finset.sum_const, Finset.sum_eq_zero, Finset.sum_eq_zero]
    have s_val : s = 0 := by
        have h : Complex.I ^ 12 = 1 := by simp [Complex.I, Complex.pow_two, Complex.pow_four, Complex.pow_six, Complex.pow_eight, Complex.pow_ten, Complex.pow_twelve]
        have h' : Complex.I ^ k = Complex.I ^ (k % 4) := by simp [mod_eq_mod]
        have h'' : ∑ k ∈ Finset.Icc 1 12, Complex.I ^ k = 0 := by
        have h : ∑ k ∈ Finset.Icc 1 12, Complex.I ^ k = ∑ k ∈ Finset.Icc 1 12, Complex.I ^ (k % 4) := by
            simp [Finset.sum_congr, Finset.Icc, Finset.sum_eq_zero]
        have h' : ∑ k ∈ Finset.Icc 1 12, Complex.I ^ (k % 4) = 0 := by
            simp [Finset.Icc, Finset.sum_eq_zero]
        exact h''
    have t_val : t = 0 := by
        have h : 1 / Complex.I ^ 12 = 1 := by simp [Complex.I, Complex.pow_two, Complex.pow_four, Complex.pow_six, Complex.pow_eight, Complex.pow_ten, Complex.pow_twelve]
        have h' : 1 / Complex.I ^ k = 1 / Complex.I ^ (k % 4) := by simp [mod_eq_mod]
        have h'' : ∑ k ∈ Finset.Icc 1 12, 1 / Complex.I ^ k = 0 := by
        have h : ∑ k ∈ Finset.Icc 1 12, 1 / Complex.I ^ k = ∑ k ∈ Finset.Icc 1 12, 1 / Complex.I ^ (k % 4) := by
            simp [Finset.sum_congr, Finset.Icc, Finset.sum_eq_zero]
        have h' : ∑ k ∈ Finset.Icc 1 12, 1 / Complex.I ^ (k % 4) = 0 := by
            simp [Finset.Icc, Finset.sum_eq_zero]
        exact h''
    have s_eq_zero : s = 0 := s_val
    have t_eq_zero : t = 0 := t_val
    have product_eq_zero : s * t = 0 := by
        have h : s = 0 := s_eq_zero
        have h' : t = 0 := t_eq_zero
        exact h * h'
    exact product_eq_zero
    """
    answer3 = Repl_Valid.write_proof(proof)
    check3 = Repl_Test.check(answer3)
    print(check3)
    print(answer3)


    Repl_Valid.close()
    Repl_Test.close()
    
"""
    ## first tests to check wrapper.py
    Repl = LEANRepl()
    Repl.import_project([], {})
    cmd1 = "example : (2:ℕ) + 2 = 4 := by rfl"
    answer1 = Repl.write_proof(cmd1)
    check1 = Repl.check(answer1)

    cmd2 = "example : (2:ℕ) + 2 = 55 := by rfl"
    answer2 = Repl.write_proof(cmd2)
    check2 = Repl.check(answer2)

    cmd3 = "example : (2:ℕ) + 2 = 4 := by sorry"
    answer3 = Repl.write_proof(cmd3)
    check3 = Repl.check(answer3)

    if(check1 == 1 and check2 == -1 and check3 == 0):
        print("the tests passed")
    else:
        if(check1 != 1):
            print("error in the correct proof")

        if(check2 != -1):
            print("error in the false proof")

        if(check3 != 0):
            print("there's still sorries in the proof")
    Repl.close()
"""
