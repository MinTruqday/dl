import os

components = {
    "DocLibHyphenationZone": {
        "is_tune": True,
        "title": "DocLib Hyphenation Zone",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M4 6H20M4 12H10M14 12H20M4 18H20\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibGutterMargin": {
        "is_tune": True,
        "title": "DocLib Gutter Margin",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M4 4V20M8 4V20M12 4H20V20H12\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibFirstLineIndent": {
        "is_tune": True,
        "title": "DocLib First Line Indent",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M10 6H20M4 12H20M4 18H20\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibPrintLayout": {
        "is_tune": True,
        "title": "DocLib Print Layout",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><rect x=\"5\" y=\"3\" width=\"14\" height=\"18\" rx=\"1\" stroke=\"currentColor\" stroke-width=\"2\"/><path d=\"M9 7H15M9 11H15M9 15H13\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/></svg>"
    },
    "DocLibReadMode": {
        "is_tune": True,
        "title": "DocLib Read Mode",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M4 19.5V4.5C4 4.5 7 3 12 5V20.5C7 18.5 4 19.5 4 19.5ZM12 5C17 3 20 4.5 20 4.5V19.5C20 19.5 17 18.5 12 20.5V5Z\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibNavigationPane": {
        "is_tune": True,
        "title": "DocLib Navigation Pane",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><rect x=\"3\" y=\"3\" width=\"18\" height=\"18\" rx=\"2\" stroke=\"currentColor\" stroke-width=\"2\"/><path d=\"M9 3V21\" stroke=\"currentColor\" stroke-width=\"2\"/><path d=\"M13 8H17M13 12H17M13 16H15\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/></svg>"
    },
    "DocLibBalloons": {
        "is_tune": True,
        "title": "DocLib Balloons",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M21 11.5C21 16.1944 16.9706 20 12 20C10.7493 20 9.55831 19.7423 8.47779 19.2789L4.5 20.5L5.75338 16.6575C4.65486 15.2536 4 13.4542 4 11.5C4 6.80558 7.58172 3 12 3C16.4183 3 21 6.80558 21 11.5Z\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibTableAutoFormat": {
        "is_block": True,
        "title": "DocLib Table AutoFormat",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><rect x=\"3\" y=\"3\" width=\"18\" height=\"18\" rx=\"2\" stroke=\"currentColor\" stroke-width=\"2\"/><path d=\"M3 9H21\" stroke=\"currentColor\" stroke-width=\"2\"/><path d=\"M9 21V9\" stroke=\"currentColor\" stroke-width=\"2\"/><path d=\"M15 9V21\" stroke=\"currentColor\" stroke-width=\"2\"/></svg>"
    },
    "DocLibDigitalSignatureLine": {
        "is_block": True,
        "title": "DocLib Digital Signature Line",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M5 15H19\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/><path d=\"M8 12L12 8L16 12\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/><path d=\"M12 18V8\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/></svg>"
    },
    "DocLibDocumentInspector": {
        "is_tune": True,
        "title": "DocLib Document Inspector",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><circle cx=\"11\" cy=\"11\" r=\"8\" stroke=\"currentColor\" stroke-width=\"2\"/><path d=\"M21 21L16.65 16.65\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/><path d=\"M11 8L11 14\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/><path d=\"M8 11L14 11\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/></svg>"
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

