from pathlib import Path
import os

def drop_comments(path):
    """takes the file given by path and errases all the comments so that the parser has a file withouth a single comment """
    p = Path(path)
    new_file = str(p.parent) + "/parser.lean"
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
                if l.lstrip().startswith("/-") and not(l.rstrip().endswith("-/")):
                    ignore = True
                else:
                    w.write(l.split("--", 1)[0] + "\n")
    w.close()





def treat_header():
    return 0
    


drop_comments("/Users/eduardo/Desktop/LEAN_AI/miniF2F/MiniF2F/Valid.lean")
