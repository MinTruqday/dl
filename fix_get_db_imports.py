import os
for root, dirs, files in os.walk("backend/authentication/src/api"):
    for file in files:
        if file.endswith(".py"):
            fpath = os.path.join(root, file)
            with open(fpath, "r") as f:
                c = f.read()
            c = c.replace(", get_db", "")
            c = c.replace("get_db,", "")
            c = c.replace("get_db", "")
            with open(fpath, "w") as f:
                f.write(c)
