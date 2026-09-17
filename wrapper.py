import subprocess
import json
import parser


class LEANRepl :

    def __init__(self) :
        """ 
            Starts the LEANRepfl as a subprocess. Once import_project is called proofs can be verified on the subprocess
        """
        self.proc = subprocess.Popen(["lake", "env", "../repl_minif2f/.lake/build/bin/repl"],
                        cwd="/Users/eduardo/Desktop/LEAN_AI/miniF2F", stdin=subprocess.PIPE, stdout=subprocess.PIPE, text = True)
        self.base_env = None

    def send(self, message):
        """
            writes the message inside the LEAN environement and returns the LEAN evaluation
            - Used only for import_project and auxiliar function in write_proof -
            - writes the message like it is, no json dumps inside -
        """
        #writing of the message
        self.proc.stdin.write(message)
        self.proc.stdin.flush()

        # reading of LEAN answer
        lines = []
        line = self.proc.stdout.readline()
        while(line != "\n") :
            if(line == "") :
                print("error on LEAN answer!!")
                break
            lines.append(line)  # the JSON response
            line = self.proc.stdout.readline()
        return json.loads("".join(lines))


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
