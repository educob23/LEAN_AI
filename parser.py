from pathlib import Path
import os

def drop_comments(path, name):
    """takes the file given by path and errases all the comments so that the parser has a file withouth a single comment """
    p = Path(path)
    new_file = str(p.parent) + f"/{name}_parser.lean"
    if os.path.exists(new_file):
        os.remove(new_file)
    w = open(new_file, "x")
    with open(path, "r") as r:
        lines = r.readlines()
        ignore = False
        for l in lines:
            if ignore == True:
                if l.rstrip().endswith("-/"):
                    ignore = False
            else:
                if l.lstrip().startswith("/-"):
                    ignore = True
                    if l.rstrip().endswith("-/"):
                        ignore = False
                else:
                    if("--" in l):
                        w.write(l.split("--", 1)[0] + "\n")
                    else:
                        w.write(l.split("--", 1)[0])
    w.close()



def treat_header(path):
    imports = []
    opens = {}
    with open(path, "r") as r:
        lines = r.readlines()
        for l in lines:
            words = l.split()
            if l.lstrip().startswith("import"):
                imports.append(words[1])
            if l.lstrip().startswith("open"):
                if(words[1] == "scoped"):
                    opens[words[2]] = 1
                else:
                    opens[words[1]] = 0
            if not l.lstrip().startswith("import") and not l.lstrip().startswith("open") and not len(words) == 0:
                break
    r.close()
    return imports, opens


def extract_theorems(path):
    """separates all theorems and returns them as a tab of strings where each string is a theorem"""
    theorems = {}
    skip = True
    with open(path, "r") as r:
        lines = r.readlines()
        theorem = ""
        thm_name = ""
        for l in lines:
            if l.lstrip().startswith("theorem"):
                if not skip:
                    # means we got to the end of the thm
                    theorems[thm_name] = theorem
                # reinit params
                theorem = ""
                skip = False
                theorem = theorem + l
                thm_name = l.split()[1]
            elif not skip:
                # we're in the middle of a thm
                theorem = theorem + l
        # for the last thm
        if not skip:
            theorems[thm_name] = theorem
    return theorems
                



     

#drop_comments("/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Valid.lean")
#imports, opens = treat_header("/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/parser.lean")

#print(imports)
#print(opens)

#theorems = extract_theorems("/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/parser.lean")
#print(theorems)
