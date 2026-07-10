import os
import re

directory = "features/compilation/components"

for filename in os.listdir(directory):
    if not filename.endswith(".ts") or filename == "index.ts":
        continue

    filepath = os.path.join(directory, filename)
    with open(filepath, "r") as f:
        content = f.read()

    # Check if the file uses the wrong format
    if content.startswith("export class "):
        name = filename.replace(".ts", "")
        # Extract title format like "DocLib Glow" from "DocLibGlow"
        spaced_name = re.sub(r"([A-Z])", r" \1", name).strip()
        lower = re.sub(r"([A-Z])", r"-\1", name).lower().lstrip("-")
        
        # We will completely replace it with the template
        template = f"""import {{ API, BlockTool }} from "@editorjs/editorjs";

export default class {name} implements BlockTool {{
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {{ content: string }};

  static get toolbox() {{
    return {{
      title: "{spaced_name}",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>'
    }};
  }}

  constructor({{ api, data }}: {{ api: API; data: any }}) {{
    this.api = api;
    this.data = {{ content: data.content || "" }};
  }}

  render() {{
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-{lower}");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.content;
    this.wrapper.dataset.placeholder = "{spaced_name}";

    this.wrapper.addEventListener("input", (e: any) => {{
      this.data.content = e.target.innerHTML;
    }});

    return this.wrapper;
  }}

  save(blockContent: HTMLElement) {{
    return {{
      content: blockContent.innerHTML
    }};
  }}
}}
"""
        with open(filepath, "w") as f:
            f.write(template)
        print(f"Fixed {filepath}")
