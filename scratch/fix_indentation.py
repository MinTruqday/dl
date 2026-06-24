import re

with open("backend/compilation/src/services/composition.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == "if True:":
        continue
    # If the previous line was "if True:" and we just removed it,
    # we need to de-indent all subsequent lines in that block by 4 spaces!
    # Or simply, let's just use `black` to format it, but `black` fails on syntax errors.
