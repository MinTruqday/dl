import os
import re

file_moves = {
    "agentic_ai/src/agents/actor.py": "agentic_ai/src/agents/actor.py",
}

for old, new in file_moves.items():
    if os.path.exists(old):
        os.rename(old, new)
        print(f"Moved {old} -> {new}")

for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                new_content = content

                # Actor renaming
                new_content = new_content.replace(
                    "src.agents.actor", "src.agents.actor"
                )
                new_content = new_content.replace("class Actor", "class Actor")
                new_content = new_content.replace("actor = Actor()", "actor = Actor()")
                new_content = new_content.replace("actor.", "actor.")
                new_content = new_content.replace(
                    "actor_agent_node", "actor_agent_node"
                )
                new_content = new_content.replace("import actor", "import actor")

                # Service -> Manager renaming
                # We specifically want to target class names like `UserManager`, `DocumentManager`
                # So we look for \w+Service

                def replace_service(match):
                    word = match.group(0)
                    # Exclude some if necessary, e.g., if there's an external library
                    if word == "Service":
                        return word
                    return word[:-7] + "Manager"

                # Replace Words ending in Service (case sensitive)
                new_content = re.sub(
                    r"\b[A-Z]\w*Service\b", replace_service, new_content
                )

                if new_content != content:
                    with open(path, "w", encoding="utf-8") as file:
                        file.write(new_content)
                    print(f"Updated {path}")
            except Exception as e:
                pass

print("Renaming completed.")
