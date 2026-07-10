import os
import re

components = {
    "DocLibFocusLine": {
        "is_tune": True,
        "title": "DocLib Focus Line",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M4 12H20M4 6H20M4 18H20\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/></svg>"
    },
    "DocLibTypewriterMode": {
        "is_tune": True,
        "title": "DocLib Typewriter Mode",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M4 8H20M4 16H20M9 4V20M15 4V20\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/></svg>"
    },
    "DocLibEditorScore": {
        "is_tune": False,
        "title": "DocLib Editor Score",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><circle cx=\"12\" cy=\"12\" r=\"10\" stroke=\"currentColor\" stroke-width=\"2\"/><path d=\"M12 6V12L16 16\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibSmartPaste": {
        "is_tune": True,
        "title": "DocLib Smart Paste",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M9 5H7C5.89543 5 5 5.89543 5 7V19C5 20.1046 5.89543 21 7 21H17C18.1046 21 19 20.1046 19 19V7C19 5.89543 18.1046 5 17 5H15M9 5C9 6.10457 9.89543 7 11 7H13C14.1046 7 15 6.10457 15 5M9 5C9 3.89543 9.89543 3 11 3H13C14.1046 3 15 3.89543 15 5\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibRevealFormatting": {
        "is_tune": True,
        "title": "DocLib Reveal Formatting",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M10 4V20M14 4V20M6 4H18\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibWidowOrphanControl": {
        "is_tune": True,
        "title": "DocLib Widow Orphan Control",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M4 6H20M4 12H12M4 18H20\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/></svg>"
    },
    "DocLibAutoCorrect": {
        "is_tune": True,
        "title": "DocLib Auto Correct",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M5 13L9 17L19 7\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibShrinkToFit": {
        "is_tune": True,
        "title": "DocLib Shrink To Fit",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M4 14L10 14M10 14V20M10 14L3 21M20 10L14 10M14 10V4M14 10L21 3\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibClearFormatting": {
        "is_tune": False,
        "inline": True,
        "title": "DocLib Clear Formatting",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M3 3L21 21M18 12H21M7 12H3\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibGoTo": {
        "is_tune": False,
        "title": "DocLib Go To",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M5 12H19M19 12L12 5M19 12L12 19\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    }
}

target_dir = "frontend/features/compilation/components"
os.makedirs(target_dir, exist_ok=True)

for name, meta in components.items():
    is_tune = meta.get("is_tune", False)
    is_inline = meta.get("inline", False)
    title = meta["title"]
    icon = meta["icon"]
    
    if is_tune:
        code = f"""import {{ API, BlockTune }} from "@editorjs/editorjs";

export default class {name} implements BlockTune {{
  static get isTune() {{
    return true;
  }}

  private api: API;
  private data: any;
  private wrapper: HTMLElement;

  constructor({{ api, data }}: {{ api: API; data: any }}) {{
    this.api = api;
    this.data = data || {{ enabled: false }};
    this.wrapper = document.createElement("div");
  }}

  render() {{
    const btn = document.createElement("button");
    btn.classList.add(this.api.styles.settingsButton);
    btn.innerHTML = `{icon}`;
    btn.dataset.title = "{title}";

    if (this.data.enabled) {{
      btn.classList.add(this.api.styles.settingsButtonActive);
    }}

    btn.addEventListener("click", () => {{
      this.data.enabled = !this.data.enabled;
      btn.classList.toggle(this.api.styles.settingsButtonActive);
    }});

    this.wrapper.appendChild(btn);
    return this.wrapper;
  }}

  save() {{
    return this.data;
  }}

  wrap(blockContent: HTMLElement) {{
    const w = document.createElement("div");
    if (this.data.enabled) {{
      w.classList.add("doclib-{name.lower()}-active");
    }}
    w.appendChild(blockContent);
    return w;
  }}
}}
"""
    elif is_inline:
        code = f"""import {{ API, InlineTool }} from "@editorjs/editorjs";

export default class {name} implements InlineTool {{
  static get isInline() {{
    return true;
  }}

  static get title() {{
    return "{title}";
  }}

  private api: API;
  private button: HTMLButtonElement | null = null;
  private tag = "SPAN";

  constructor({{ api }}: {{ api: API }}) {{
    this.api = api;
  }}

  render() {{
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = `{icon}`;
    return this.button;
  }}

  surround(range: Range) {{
    if (!range) return;
    const termWrapper = this.api.selection.findParentTag(this.tag, "{name}");
    if (termWrapper) {{
      this.unwrap(termWrapper);
    }} else {{
      this.wrap(range);
    }}
  }}

  wrap(range: Range) {{
    const el = document.createElement(this.tag);
    el.classList.add("{name}");
    el.appendChild(range.extractContents());
    range.insertNode(el);
    this.api.selection.expandToTag(el);
  }}

  unwrap(termWrapper: HTMLElement) {{
    this.api.selection.expandToTag(termWrapper);
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0) {{
      const range = sel.getRangeAt(0);
      const unwrappedContent = range.extractContents();
      termWrapper.parentNode?.removeChild(termWrapper);
      range.insertNode(unwrappedContent);
      sel.removeAllRanges();
      sel.addRange(range);
    }}
  }}

  checkState() {{
    const termWrapper = this.api.selection.findParentTag(this.tag, "{name}");
    if (this.button) {{
      this.button.classList.toggle(
        this.api.styles.inlineToolButtonActive,
        !!termWrapper
      );
    }}
    return !!termWrapper;
  }}
}}
"""
    else:
        code = f"""import {{ API, BlockTool, BlockToolData }} from "@editorjs/editorjs";

export default class {name} implements BlockTool {{
  static get toolbox() {{
    return {{
      title: "{title}",
      icon: `{icon}`,
    }};
  }}

  private api: API;
  private data: BlockToolData;
  private wrapper: HTMLElement;

  constructor({{ api, data }}: {{ api: API; data: BlockToolData }}) {{
    this.api = api;
    this.data = data || {{ content: "" }};
    this.wrapper = document.createElement("div");
  }}

  render() {{
    this.wrapper.classList.add("ce-block");
    const input = document.createElement("input");
    input.classList.add("ce-paragraph", "cdx-block");
    input.value = this.data.content || "";
    input.placeholder = "{title}";
    this.wrapper.appendChild(input);
    return this.wrapper;
  }}

  save(blockContent: HTMLElement) {{
    const input = blockContent.querySelector("input") as HTMLInputElement;
    return {{
      content: input ? input.value : "",
    }};
  }}
}}
"""
    with open(os.path.join(target_dir, f"{name}.ts"), "w", encoding="utf-8") as f:
        f.write(code)

